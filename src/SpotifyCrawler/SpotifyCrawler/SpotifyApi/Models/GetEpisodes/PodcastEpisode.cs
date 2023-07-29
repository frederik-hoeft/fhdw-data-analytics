using SpotifyCrawler.Ranking.Model;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Text.Json.Serialization;

namespace SpotifyCrawler.SpotifyApi.Models.GetEpisodes;

public record PodcastEpisode
(
    [property: JsonPropertyName("duration_ms")] long DurationMs,
    [property: JsonPropertyName("explicit")] bool Explicit,
    [property: JsonPropertyName("href")] Uri Href,
    [property: JsonPropertyName("id")] string SpotifyId,
    [property: JsonPropertyName("is_externally_hosted")] bool IsExternallyHosted,
    [property: JsonPropertyName("is_playable")] bool IsPlayable,
    [property: JsonPropertyName("language")] string Language,
    [property: JsonPropertyName("release_date")] DateOnly ReleaseDate,
    [property: JsonPropertyName("release_date_precision")] string ReleaseDatePrecision,
    [property: JsonPropertyName("type")] string Type,
    [property: JsonPropertyName("uri")] string SpotifyUri
)
{
    [Key]
    [JsonIgnore]
    public int Id { get; set; }

    [JsonPropertyName("description")]
    public string Description { get; set; } = null!;

    [JsonPropertyName("name")]
    public string Name { get; set; } = null!;

    [JsonPropertyName("images")]
    public virtual List<Image> Images { get; set; } = null!;

    [JsonIgnore]
    public virtual Podcast Podcast { get; set; } = null!;
}
