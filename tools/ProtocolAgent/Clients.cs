using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json.Nodes;

namespace ProtocolAgent;

internal sealed class ApiClient : IDisposable
{
    private readonly HttpClient client;
    public string Server { get; }

    public ApiClient(string url, string token)
    {
        var uri = new Uri(url.TrimEnd('/') + "/");
        if (uri.Scheme != "https" && !(uri.Scheme == "http" && uri.IsLoopback))
            throw new ArgumentException("API должен использовать HTTPS (HTTP разрешён для localhost).");
        Server = uri.AbsoluteUri;
        client = new HttpClient(new HttpClientHandler { AllowAutoRedirect = false })
        { BaseAddress = uri, Timeout = TimeSpan.FromMinutes(5) };
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
    }

    public async Task<JsonNode> Get(string path, CancellationToken ct)
    {
        using var response = await client.GetAsync(path.TrimStart('/'), ct);
        return await Read(response, ct);
    }

    public async Task<JsonNode> Post(string path, JsonNode body, CancellationToken ct)
    {
        // No blind retries: the caller persists requests before any mutation.
        using var response = await client.PostAsJsonAsync(path.TrimStart('/'), body, ct);
        return await Read(response, ct);
    }

    private static async Task<JsonNode> Read(HttpResponseMessage response, CancellationToken ct)
    {
        var text = await response.Content.ReadAsStringAsync(ct);
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException($"FinCubes HTTP {(int)response.StatusCode}: {text[..Math.Min(text.Length, 2500)]}");
        return JsonNode.Parse(text) ?? throw new InvalidOperationException("Пустой JSON от API.");
    }

    public void Dispose() => client.Dispose();
}

internal sealed class ModelClient : IDisposable
{
    private readonly HttpClient client;
    private readonly string model;

    public ModelClient(string key, string model)
    {
        this.model = model;
        client = new HttpClient { BaseAddress = new Uri("https://api.openai.com/v1/"), Timeout = TimeSpan.FromMinutes(15) };
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", key);
    }

    public async Task<JsonObject> Ask(string instructions, string prompt, JsonObject schema,
        CancellationToken ct, string? pdf = null)
    {
        var content = new JsonArray(new JsonObject { ["type"] = "input_text", ["text"] = prompt });
        if (pdf is not null)
        {
            if (new FileInfo(pdf).Length > 40 * 1024 * 1024)
                throw new InvalidOperationException("PDF больше локального лимита 40 МБ; разделите документ на части.");
            content.Add(new JsonObject
            {
                ["type"] = "input_file", ["filename"] = Path.GetFileName(pdf),
                ["file_data"] = "data:application/pdf;base64," + Convert.ToBase64String(await File.ReadAllBytesAsync(pdf, ct))
            });
        }
        var body = new JsonObject
        {
            ["model"] = model, ["store"] = false, ["instructions"] = instructions,
            ["input"] = new JsonArray(new JsonObject { ["role"] = "user", ["content"] = content }),
            ["text"] = new JsonObject { ["format"] = new JsonObject
            { ["type"] = "json_schema", ["name"] = "protocol_agent", ["strict"] = true, ["schema"] = schema.DeepClone() } }
        };
        using var response = await client.PostAsJsonAsync("responses", body, ct);
        var text = await response.Content.ReadAsStringAsync(ct);
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException($"OpenAI HTTP {(int)response.StatusCode}: {text[..Math.Min(text.Length, 1500)]}");
        var data = JsonNode.Parse(text) ?? throw new InvalidOperationException("Пустой ответ модели.");
        if (data["status"]?.ToString() != "completed")
            throw new InvalidOperationException("Модель не завершила ответ; импорт не продолжается с обрезанными данными.");
        var output = new List<string>();
        foreach (var item in data["output"]!.AsArray())
        foreach (var part in item?["content"]?.AsArray() ?? [])
        {
            if (part?["type"]?.ToString() == "refusal") throw new InvalidOperationException("Модель отказалась обработать документ.");
            if (part?["type"]?.ToString() == "output_text") output.Add(part["text"]!.ToString());
        }
        return JsonNode.Parse(string.Concat(output))?.AsObject()
            ?? throw new InvalidOperationException("Модель не вернула JSON-объект.");
    }

    public void Dispose() => client.Dispose();
}
