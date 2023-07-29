using System.Text.Json;

namespace SpotifyCrawler;

public record Secrets(string SpotifyClientId, string SpotifyClientSecret)
{
    public static Secrets LoadFromFile(string filename)
    {
        using Stream stream = File.OpenRead(filename);
        return JsonSerializer.Deserialize<Secrets>(stream)
            ?? throw new InvalidOperationException($"Unable to load Spotify client secrets from '{filename}'.");
    }
}