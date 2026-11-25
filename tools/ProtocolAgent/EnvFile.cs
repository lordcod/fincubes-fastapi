using System.Text;

namespace ProtocolAgent;

internal static class EnvFile
{
    public static readonly string[] Keys = ["FINCUBES_API_URL", "FINCUBES_API_TOKEN", "OPENAI_API_KEY", "OPENAI_MODEL", "PROTOCOL_AGENT_STATE"];

    public static string Find()
    {
        var besideExe = Path.Combine(AppContext.BaseDirectory, ".env");
        if (File.Exists(besideExe)) return besideExe;
        foreach (var origin in new[] { Environment.CurrentDirectory, AppContext.BaseDirectory })
        for (var dir = new DirectoryInfo(origin); dir is not null; dir = dir.Parent)
        {
            foreach (var relative in new[] { "tools/ProtocolAgent/.env", "ProtocolAgent/.env" })
            {
                var path = Path.Combine(dir.FullName, relative);
                if (File.Exists(path)) return path;
            }
            if (dir.Name == "ProtocolAgent" && File.Exists(Path.Combine(dir.FullName, ".env")))
                return Path.Combine(dir.FullName, ".env");
        }
        return besideExe;
    }

    public static void Load(string path)
    {
        if (!File.Exists(path)) return;
        foreach (var line in File.ReadAllLines(path))
        {
            var trimmed = line.Trim();
            if (trimmed.StartsWith('#') || !trimmed.Contains('=')) continue;
            var parts = trimmed.Split('=', 2);
            var key = parts[0].Trim();
            if (!Keys.Contains(key)) continue;
            var value = parts[1].Trim();
            if (value.Length >= 2 && ((value[0] == '"' && value[^1] == '"') || (value[0] == '\'' && value[^1] == '\'')))
                value = value[1..^1];
            Environment.SetEnvironmentVariable(key, value);
        }
    }

    public static void Save(string path, Dictionary<string, string> values)
    {
        foreach (var value in values.Values)
            if (value.Contains('\n') || value.Contains('\r')) throw new ArgumentException("Настройки должны занимать одну строку.");
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
        var content = "# Local settings; do not commit or share this file.\n" +
            string.Join("\n", Keys.Select(key => $"{key}={values.GetValueOrDefault(key, "")}")) + "\n";
        File.WriteAllText(path + ".tmp", content, new UTF8Encoding(false));
        File.Move(path + ".tmp", path, true);
        Load(path);
    }
}
