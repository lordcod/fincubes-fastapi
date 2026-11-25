using System.Text.Json.Nodes;
using PdfSharp.Pdf;
using PdfSharp.Pdf.IO;

namespace ProtocolAgent;

internal sealed partial class ImportAgent
{
    private async Task<JsonObject> ExtractPdf(string file)
    {
        using var pdf = PdfReader.Open(file, PdfDocumentOpenMode.Import);
        if (pdf.PageCount == 0) throw new InvalidOperationException("В PDF нет страниц.");
        state["pdf_pages"] ??= new JsonObject();
        var completed = state["pdf_pages"]!.AsObject();
        var guide = await File.ReadAllTextAsync(Path.Combine(AppContext.BaseDirectory, "protocol-import.md"), ct);
        JsonObject? firstCompetition = null;
        for (var index = 0; index < pdf.PageCount; index++)
        {
            ct.ThrowIfCancellationRequested();
            var number = index + 1;
            var key = number.ToString();
            if (completed[key]?["complete"]?.GetValue<bool>() == true)
            {
                firstCompetition ??= completed[key]!["competition"]!.DeepClone().AsObject();
                Console.WriteLine($"Страница {number}/{pdf.PageCount} — уже обработана.");
                continue;
            }
            Console.WriteLine($"Извлекаю страницу {number}/{pdf.PageCount}…");
            var pagePath = Path.Combine(folder, $"page-{number}.pdf");
            var from = Math.Max(0, index - 1);
            var to = Math.Min(pdf.PageCount - 1, index + 1);
            using (var segment = new PdfDocument())
            {
                for (var p = from; p <= to; p++) segment.AddPage(pdf.Pages[p]);
                segment.Save(pagePath);
            }
            var prompt = $"Это фрагмент исходного PDF, страницы {from + 1}–{to + 1}. " +
                $"Извлеки результаты ТОЛЬКО исходной страницы {number}, это страница {index - from + 1} приложенного фрагмента. " +
                "Соседние страницы нужны только для заголовков/продолжения таблицы. Не копируй их результаты. " +
                $"metadata.source_page всегда {number}. Верни все подходящие строки целевой страницы. " +
                "complete относится ТОЛЬКО к этой странице: если подходящих дисциплин нет, complete=true, athletes=[], teams=[]. " +
                "Не останавливайся из-за большого размера ОРИГИНАЛА — от тебя требуется одна страница. " +
                "Не сливай разные строки времени и DNS в одну запись. Для неизвестной команды сохрани alias='Без команды', " +
                "city=null, region=null, не выдумывай организацию. ФИО/год не восстанавливай догадкой. " +
                "organizer='' если неизвестен, links=[] при отсутствии ссылок, даты yyyy-MM-dd. " +
                "Если заголовок не повторяется, используй переданный контекст соревнования и предыдущего раздела. " +
                "Контекст пользователя:\n" + S(state, "context") +
                "\nСоревнование:\n" + (firstCompetition?.ToJsonString() ?? "Извлеки из первой страницы") +
                "\nПоследние заголовки предыдущей страницы:\n" +
                (index > 0 ? string.Join("\n", Items(completed[index.ToString()]?["athletes"])
                    .SelectMany(a => Items(a["results"])).TakeLast(4).Select(r => r["metadata"]?.ToJsonString())) : "нет");
            JsonObject? page = null;
            for (var attempt = 0; attempt < 2; attempt++)
            {
                page = await model.Ask(Policy + "\n" + guide, prompt, Schemas.Extraction(), ct, pagePath);
                completed[key] = page.DeepClone();
                await Save();
                if (page["complete"]?.GetValue<bool>() == true) break;
                Console.WriteLine($"Уточняю извлечение страницы {number}…");
                prompt += "\nПредыдущая попытка неполная. Исправь причины, не возвращай сокращённую выборку: " + page["issues"]?.ToJsonString();
            }
            if (page?["complete"]?.GetValue<bool>() != true)
            {
                Console.WriteLine("Нужен факт для страницы " + number + ": " +
                    string.Join("; ", Items(page?["issues"]).Select(i => i.ToString())));
                Console.Write("Напиши уточнение (Enter — остановить с сохранением готовых страниц): ");
                var clarification = Console.ReadLine();
                if (string.IsNullOrWhiteSpace(clarification)) throw new InvalidOperationException($"Остановлено на странице {number}. Готовые страницы сохранены.");
                state["context"] = S(state, "context") + $"\nСтраница {number}: " + clarification;
                await Save();
                page = await model.Ask(Policy + "\n" + guide, prompt + "\nУточнение пользователя: " + clarification,
                    Schemas.Extraction(), ct, pagePath);
                completed[key] = page.DeepClone();
                await Save();
                if (page["complete"]?.GetValue<bool>() != true) throw new InvalidOperationException($"Страница {number} всё ещё неполная; остальные данные сохранены.");
            }
            firstCompetition ??= page!["competition"]!.DeepClone().AsObject();
        }
        var teams = new JsonArray();
        var athletes = new JsonArray();
        var issues = new JsonArray();
        var teamIdentities = new Dictionary<string, string>();
        for (var index = 1; index <= pdf.PageCount; index++)
        {
            var page = completed[index.ToString()]!;
            var teamMap = new Dictionary<string, string>();
            foreach (var team in Items(page["teams"]))
            {
                var identity = string.Join("|", new[] { "alias", "city", "region" }.Select(f => N(S(team, f))));
                if (!teamIdentities.TryGetValue(identity, out var mapped))
                {
                    mapped = "t" + (teams.Count + 1);
                    teamIdentities[identity] = mapped;
                    var copy = team.DeepClone(); copy["key"] = mapped; teams.Add(copy);
                }
                teamMap[S(team, "key")] = mapped;
            }
            foreach (var athlete in Items(page["athletes"]))
            {
                var copy = athlete.DeepClone();
                copy["key"] = $"p{index}-{S(athlete, "key")}";
                copy["team_key"] = teamMap[S(athlete, "team_key")];
                foreach (var result in Items(copy["results"]))
                {
                    result["metadata"] ??= new JsonObject();
                    result["metadata"]!["source_page"] = index;
                }
                athletes.Add(copy);
            }
            foreach (var issue in Items(page["issues"])) issues.Add($"Страница {index}: {issue}");
        }
        Console.WriteLine($"Извлечение завершено: {pdf.PageCount} страниц, {athletes.Count} записей участников.");
        return new JsonObject { ["complete"] = true, ["issues"] = issues, ["competition"] = firstCompetition,
            ["teams"] = teams, ["athletes"] = athletes };
    }
}
