using SpotifyCrawler.Attributes;
using SpotifyCrawler.Data;
using SpotifyCrawler.Ranking.Converters;
using SpotifyCrawler.Ranking.Model;
using SpotifyCrawler.SpotifyApi.Models;
using SpotifyCrawler.SpotifyApi.Models.GetEpisodes;
using System.Net;
using System.Net.Http.Headers;
using System.Text.Json;

namespace SpotifyCrawler.SpotifyApi;

public sealed class SpotifyClient : IDisposable
{
    private static readonly JsonSerializerOptions _jsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    private readonly HttpClient _httpClient;
    private readonly Secrets _secrets;
    private readonly UnicodeSanitizer _sanitizer;

    public SpotifyClient(Secrets secrets)
    {
        _secrets = secrets;
        _httpClient = new HttpClient(new HttpClientHandler()
        {
            AllowAutoRedirect = true,
            UseCookies = true
        })
        {
            BaseAddress = new Uri("https://api.spotify.com")
        };
        _sanitizer = new UnicodeSanitizer();
    }

    public bool Authenticate()
    {
        _httpClient.DefaultRequestHeaders.Remove("Authorization");
        using HttpRequestMessage request = new(HttpMethod.Post, "https://accounts.spotify.com/api/token");
        Dictionary<string, string> formContent = new()
        {
            { "grant_type", "client_credentials" },
            { "client_id", _secrets.SpotifyClientId },
            { "client_secret", _secrets.SpotifyClientSecret },
        };
        using FormUrlEncodedContent content = new(formContent);
        request.Content = content;
        using HttpResponseMessage response = _httpClient.Send(request);
        Console.WriteLine($"{response.StatusCode}: {request.Method} {request.RequestUri}");
        if (!response.IsSuccessStatusCode)
        {
            return false;
        }
        using Stream stream = response.Content.ReadAsStream();
        TokenResponse? token = JsonSerializer.Deserialize<TokenResponse>(stream, _jsonOptions);
        if (token?.AccessToken is null or "")
        {
            return false;
        }
        _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token.AccessToken);
        return true;
    }

    private int delay = 0;

    public bool TryFetchEpisodes(SqliteContext dbContext, Podcast podcast)
    {
        const int RETRY_COUNT = 10;
        for (int showRetry = 0; showRetry < RETRY_COUNT; showRetry++)
        {
            string showId = podcast.ShowUri[^22..];
            string marketCode = podcast.Market.GetAttributeValue<CountryCode, JsonValueAttribute>(attr => attr.Value)?.ToUpperInvariant()
                ?? throw new InvalidOperationException($"unable to retrieve JSON value of market '{podcast.Market}'");
            string requestUri = $"/v1/shows/{showId}?market={marketCode}";
            using HttpRequestMessage showRequest = new(HttpMethod.Get, $"/v1/shows/{showId}?market={marketCode}");
            using HttpResponseMessage showResponse = _httpClient.Send(showRequest);
            Console.WriteLine($"{showResponse.StatusCode}: {showRequest.Method} {showRequest.RequestUri}");
            if (!showResponse.IsSuccessStatusCode)
            {
                if (showResponse.StatusCode is HttpStatusCode.Unauthorized)
                {
                    Authenticate();
                }
                if (showResponse.StatusCode is HttpStatusCode.GatewayTimeout)
                {
                    delay += 500;
                    Console.WriteLine($"[WARN] increased retry delay to {delay} ms.");
                }
                Console.WriteLine($"[WARN] show retry {showRetry + 1} of {RETRY_COUNT} in {delay} ms...");
                Thread.Sleep(delay);
                continue;
            }
            showResponse.EnsureSuccessStatusCode();
            using Stream initialStream = showResponse.Content.ReadAsStream();
            ShowDetails? showDetails = JsonSerializer.Deserialize<ShowDetails>(initialStream, _jsonOptions)
                ?? throw new InvalidOperationException($"{nameof(showDetails)} was null :C");
            podcast.IsExplicit = showDetails.Explicit;
            List<PodcastEpisode> episodes = showDetails.CurrentPage.Episodes;
            EpisodeResultPage? currentPage = showDetails.CurrentPage;
            for (string? uri = currentPage.Next; !string.IsNullOrEmpty(uri); uri = currentPage.Next)
            {
                currentPage = null;
                int pageDelay = 0;
                for (int pageRetry = 0; pageRetry < RETRY_COUNT; pageRetry++)
                {
                    using HttpRequestMessage request = new(HttpMethod.Get, uri);
                    using HttpResponseMessage response = _httpClient.Send(request);
                    Console.WriteLine($"{response.StatusCode}: {request.Method} {request.RequestUri}");
                    if (!response.IsSuccessStatusCode)
                    {
                        if (response.StatusCode is HttpStatusCode.Unauthorized)
                        {
                            Authenticate();
                        }
                        if (response.StatusCode is HttpStatusCode.GatewayTimeout)
                        {
                            pageDelay += 500;
                            Console.WriteLine($"[WARN] increased page retry delay to {delay + pageDelay} ms.");
                        }
                        Console.WriteLine($"[WARN] page retry {pageRetry + 1} of {RETRY_COUNT} in {delay + pageDelay} ms...");
                        Thread.Sleep(delay);
                        continue;
                    }
                    using Stream stream = response.Content.ReadAsStream();
                    currentPage = JsonSerializer.Deserialize<EpisodeResultPage>(stream, _jsonOptions)
                        ?? throw new InvalidOperationException($"{nameof(episodes)} was null :C");
                    break;
                }
                if (currentPage is null)
                {
                    Console.WriteLine($"[WARN] exceeded retry counter waiting for {uri}... skipping this podcast :/");
                    return false;
                }
                episodes.AddRange(currentPage.Episodes);
            }
            if (showDetails.TotalEpisodes != episodes.Count)
            {
                Console.WriteLine($"[WARN] expected {showDetails.TotalEpisodes} episodes to be returned, but retrieved {episodes.Count}. This is sus");
            }
            podcast.Episodes ??= new List<PodcastEpisode>();
            foreach (PodcastEpisode episode in episodes)
            {
                foreach (Image image in episode.Images)
                {
                    image.Episode = episode;
                }
                episode.Podcast = podcast;
                episode.Name = _sanitizer.EscapeToAscii(episode.Name);
                episode.Description = _sanitizer.EscapeToAscii(episode.Description);
                podcast.Episodes.Add(episode);
            }
            int changed = dbContext.SaveChanges();
            Console.WriteLine($"{changed} entries written to DB");
            return true;
        }
        return false;
    }

    public void Dispose() => _httpClient.Dispose();
}
