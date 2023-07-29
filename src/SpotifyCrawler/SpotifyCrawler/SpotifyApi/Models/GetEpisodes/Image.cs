using Microsoft.EntityFrameworkCore;
using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace SpotifyCrawler.SpotifyApi.Models.GetEpisodes;

public record Image
(
    [property: JsonPropertyName("height")] long Height,
    [property: JsonPropertyName("url")] Uri Url,
    [property: JsonPropertyName("width")] long Width
)
{
    [Key]
    [JsonIgnore]
    public int Id { get; set; }

    [JsonIgnore]
    public virtual PodcastEpisode Episode { get; set; } = null!;
}