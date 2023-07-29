using System.Text.Json.Serialization;

namespace SpotifyCrawler.SpotifyApi.Models.GetEpisodes;

public record EpisodeResultPage
(
    [property: JsonPropertyName("href")] Uri Href,
    [property: JsonPropertyName("items")] List<PodcastEpisode> Episodes,
    [property: JsonPropertyName("limit")] long Limit,
    [property: JsonPropertyName("next")] string? Next,
    [property: JsonPropertyName("offset")] long Offset,
    [property: JsonPropertyName("previous")] string? Previous,
    [property: JsonPropertyName("total")] long Total
);