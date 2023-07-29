using System.Text.Json.Serialization;

namespace SpotifyCrawler.SpotifyApi.Models;

public record TokenResponse
(
    [property: JsonPropertyName("access_token")] string AccessToken,
    [property: JsonPropertyName("token_type")] string TokenType,
    [property: JsonPropertyName("expires_in")] long ExpiresIn
);
