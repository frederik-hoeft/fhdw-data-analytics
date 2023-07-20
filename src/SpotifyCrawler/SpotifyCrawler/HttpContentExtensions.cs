using System.Text.Json;

namespace SpotifyCrawler;

public static class HttpContentExtensions
{
    public static T? ReadFromJson<T>(this HttpContent content, JsonSerializerOptions? options = null)
    {
        using Stream stream = content.ReadAsStream();
        using StreamReader reader = new(stream);
        string json = reader.ReadToEnd();
        return JsonSerializer.Deserialize<T>(json, options);
    }
}
