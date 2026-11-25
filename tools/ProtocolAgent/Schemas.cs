using System.Text.Json.Nodes;

namespace ProtocolAgent;

internal static class Schemas
{
    private static JsonObject Text(bool nullable = false) => nullable
        ? new JsonObject { ["type"] = new JsonArray("string", "null") }
        : new JsonObject { ["type"] = "string" };
    private static JsonObject Number() => new() { ["type"] = "integer" };
    private static JsonObject Boolean() => new() { ["type"] = "boolean" };
    private static JsonObject Enum(params string[] values) => new()
    { ["type"] = "string", ["enum"] = new JsonArray(values.Select(v => (JsonNode?)JsonValue.Create(v)).ToArray()) };
    private static JsonObject Array(JsonObject item) => new() { ["type"] = "array", ["items"] = item };
    internal static JsonObject Obj(params (string Key, JsonObject Value)[] fields) => new()
    {
        ["type"] = "object", ["additionalProperties"] = false,
        ["properties"] = new JsonObject(fields.Select(f => KeyValuePair.Create<string, JsonNode?>(f.Key, f.Value))),
        ["required"] = new JsonArray(fields.Select(f => (JsonNode?)JsonValue.Create(f.Key)).ToArray())
    };

    public static JsonObject Extraction()
    {
        var metadata = Obj(("source_page", Number()), ("source_text", Text()),
            ("discipline_raw", Text()), ("category", Text(true)), ("round", Text(true)));
        var result = Obj(("stroke", Enum("APNEA", "BIFINS", "IMMERSION", "SURFACE")),
            ("distance", Number()), ("result", Text(true)), ("final", Text(true)),
            ("place", Text(true)), ("final_rank", Text(true)), ("points", Text(true)), ("record", Text(true)),
            ("status", Enum("COMPLETED", "QUALIFIED", "EXH", "DNS", "DNF", "WDR", "DSQ", "DSQ_FINAL")),
            ("metadata", metadata));
        var athlete = Obj(("key", Text()), ("team_key", Text()), ("last_name", Text()),
            ("first_name", Text()), ("birth_year", Number()), ("gender", Enum("M", "F")),
            ("license", Text(true)), ("results", Array(result)));
        var competition = Obj(("name", Text()), ("date", Text()), ("location", Text()),
            ("city", Text(true)), ("organizer", Text()), ("course", Text(true)),
            ("status", Text(true)), ("links", Array(Text())), ("start_date", Text()), ("end_date", Text()));
        return Obj(("complete", Boolean()), ("issues", Array(Text())), ("competition", competition),
            ("teams", Array(Obj(("key", Text()), ("alias", Text()), ("city", Text(true)), ("region", Text(true))))),
            ("athletes", Array(athlete)));
    }

    public static JsonObject Choice() => Obj(("action", Enum("existing", "create", "ask")),
        ("id", Text(true)), ("reason", Text()));

    public static JsonObject LocationChoice() => Obj(("action", Enum("existing", "create", "ask")),
        ("id", Text(true)), ("reason", Text()), ("club", Text(true)), ("city", Text(true)),
        ("region", Text(true)), ("required", Array(Enum("city", "region"))));
}
