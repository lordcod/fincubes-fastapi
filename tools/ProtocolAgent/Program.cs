using System.Text;
using System.Text.Json.Nodes;
using ProtocolAgent;

Console.OutputEncoding = Encoding.UTF8;
if (args.Length == 0 || args.Contains("--help"))
{
    Console.WriteLine("""
        ProtocolAgent — локальный агент импорта подводного спорта
        dotnet run --project tools/ProtocolAgent -- protocol.pdf [--context context.txt] [--competition-id 123]
        Также поддержаны .txt и .json (готовое извлечение в формате extraction.json).
        Настройки окружения:
          FINCUBES_API_URL   URL API, например http://localhost:8001/
          FINCUBES_API_TOKEN токен со scopes competition:read,create; athlete:read; protocol:import
          OPENAI_API_KEY    ключ OpenAI API
          OPENAI_MODEL      модель с поддержкой PDF и Structured Outputs
          PROTOCOL_AGENT_STATE каталог состояния (по умолчанию LocalApplicationData/FinCubes/ProtocolAgent)
        Документ и кандидаты отправляются в OpenAI; ключи в журнал не сохраняются.
        Запуск выполняет запись на сервер без промежуточных подтверждений.
        """);
    return 0;
}

using var cancellation = new CancellationTokenSource();
Console.CancelKeyPress += (_, e) => { e.Cancel = true; cancellation.Cancel(); };
try
{
    EnvFile.Load(EnvFile.Find());
    string Required(string name) => Environment.GetEnvironmentVariable(name) is { Length: > 0 } value
        ? value : throw new InvalidOperationException($"Задайте {name}.");
    string? context = null;
    int? competitionId = null;
    for (var i = 1; i < args.Length; i++)
    {
        if (i + 1 >= args.Length) throw new ArgumentException("Пропущено значение аргумента.");
        switch (args[i])
        {
            case "--context": context = await File.ReadAllTextAsync(args[++i], cancellation.Token); break;
            case "--competition-id": competitionId = int.Parse(args[++i]); break;
            default: throw new ArgumentException($"Неизвестный аргумент: {args[i]}");
        }
    }
    var configuredRoot = Environment.GetEnvironmentVariable("PROTOCOL_AGENT_STATE");
    var root = string.IsNullOrWhiteSpace(configuredRoot)
        ? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "FinCubes", "ProtocolAgent") : configuredRoot;
    Directory.CreateDirectory(root);
    // One local worker prevents concurrent creation of the same competition by this installation.
    using var jobLock = new FileStream(Path.Combine(root, "agent.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
    using var api = new ApiClient(Required("FINCUBES_API_URL"), Required("FINCUBES_API_TOKEN"));
    using var model = new ModelClient(Required("OPENAI_API_KEY"), Required("OPENAI_MODEL"));
    var agent = new ImportAgent(api, model, root, cancellation.Token);
    await agent.Run(Path.GetFullPath(args[0].Trim().Trim('"')), context, competitionId);
    return 0;
}
catch (OperationCanceledException)
{
    Console.Error.WriteLine("Остановлено. Повторите ту же команду для продолжения.");
    return 130;
}
catch (Exception exception)
{
    Console.Error.WriteLine(exception.Message);
    Console.Error.WriteLine("Состояние сохранено. Повторный запуск продолжит тот же импорт.");
    return 1;
}
