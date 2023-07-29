using System.Text.Json.Serialization;

namespace SpotifyCrawler.SpotifyApi.Models.GetEpisodes;

public record ShowDetails
(
    [property: JsonPropertyName("available_markets")] string[] AvailableMarkets,
    [property: JsonPropertyName("description")] string Description,
    [property: JsonPropertyName("episodes")] EpisodeResultPage CurrentPage,
    [property: JsonPropertyName("explicit")] bool Explicit,
    [property: JsonPropertyName("href")] Uri Href,
    [property: JsonPropertyName("html_description")] string HtmlDescription,
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("images")] Image[] Images,
    [property: JsonPropertyName("is_externally_hosted")] bool IsExternallyHosted,
    [property: JsonPropertyName("languages")] string[] Languages,
    [property: JsonPropertyName("media_type")] string MediaType,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("publisher")] string Publisher,
    [property: JsonPropertyName("total_episodes")] long TotalEpisodes,
    [property: JsonPropertyName("type")] string Type,
    [property: JsonPropertyName("uri")] string Uri
);