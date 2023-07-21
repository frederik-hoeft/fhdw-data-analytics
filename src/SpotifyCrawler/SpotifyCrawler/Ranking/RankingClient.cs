using SpotifyCrawler.Attributes;
using SpotifyCrawler.Data;
using SpotifyCrawler.Output;
using SpotifyCrawler.Ranking.Converters;
using SpotifyCrawler.Ranking.Model;
using System.Text.Json;

namespace SpotifyCrawler.Ranking;

public sealed class RankingClient : IDisposable
{
    private static readonly JsonSerializerOptions _jsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    private readonly HttpClient _httpClient;
    private readonly UnicodeSanitizer _sanitizer;

    public RankingClient()
    {
        _httpClient = new HttpClient(new HttpClientHandler()
        {
            AllowAutoRedirect = true,
            UseCookies = true
        })
        {
            BaseAddress = new Uri("https://podcastcharts.byspotify.com")
        };
        _sanitizer = new UnicodeSanitizer();
    }

    public PodcastRanking GetRankingForCountry(SqliteContext dbContext, CountryCode countryCode)
    {
        string? regionCode = countryCode.GetAttributeValue<CountryCode, JsonValueAttribute>(attr => attr.Value);
        using HttpRequestMessage request = new(HttpMethod.Get, $"/api/charts/top?region={regionCode}");
        using HttpResponseMessage response = _httpClient.Send(request);
        Console.WriteLine($"{response.StatusCode}: {request.Method} {request.RequestUri}");
        Podcast[] podcasts = response.Content.ReadFromJson<Podcast[]>(_jsonOptions)
            ?? throw new InvalidOperationException("failed to deserialize response!");
        PodcastRanking ranking = new(GenreType.All, countryCode)
        {
            Podcasts = new List<RankedPodcast>()
        };
        dbContext.Add(ranking);
        for (int i = 0; i < podcasts.Length; i++)
        {
            Podcast? podcast = dbContext.Podcasts.SingleOrDefault(p => p.ShowUri.Equals(podcasts[i].ShowUri));
            if (podcast is null)
            {
                podcast = podcasts[i];
                podcast.ShowDescription = _sanitizer.EscapeToAscii(podcast.ShowDescription);
                podcast.ShowName = _sanitizer.EscapeToAscii(podcast.ShowName);
                podcast.ShowPublisher = _sanitizer.EscapeToAscii(podcast.ShowPublisher);
                dbContext.Add(podcast);
            }
            ranking.Podcasts.Add(new RankedPodcast(i + 1)
            {
                Ranking = ranking,
                Podcast = podcast,
            });
        }
        return ranking;
    }

    public PodcastRanking? GetRankingForCountry(SqliteContext dbContext, CountryCode countryCode, GenreType genreType)
    {
        string? regionCode = countryCode.GetAttributeValue<CountryCode, JsonValueAttribute>(attr => attr.Value);
        string? genreEndpoint = genreType.GetAttributeValue<GenreType, ApiEndpointAttribute>(attr => attr.Endpoint);
        using HttpRequestMessage request = new(HttpMethod.Get, $"/api/charts/{genreEndpoint}?region={regionCode}");
        using HttpResponseMessage response = _httpClient.Send(request);
        Console.WriteLine($"{response.StatusCode}: {request.Method} {request.RequestUri}");
        if (!response.IsSuccessStatusCode)
        {
            return null;
        }
        Podcast[] podcasts = response.Content.ReadFromJson<Podcast[]>(_jsonOptions)
            ?? throw new InvalidOperationException("failed to deserialize response!");
        PodcastRanking ranking = new(genreType, countryCode)
        {
            Podcasts = new List<RankedPodcast>()
        };
        dbContext.Add(ranking);
        for (int i = 0; i < podcasts.Length; i++)
        {
            Podcast? podcast = dbContext.Podcasts.SingleOrDefault(p => p.ShowUri.Equals(podcasts[i].ShowUri));
            if (podcast is null)
            {
                podcast = podcasts[i];
                podcast.ShowDescription = _sanitizer.EscapeToAscii(podcast.ShowDescription);
                podcast.ShowName = _sanitizer.EscapeToAscii(podcast.ShowName);
                podcast.ShowPublisher = _sanitizer.EscapeToAscii(podcast.ShowPublisher);
                dbContext.Add(podcast);
            }
            else
            {
                podcast.Genre = genreType;
            }
            ranking.Podcasts.Add(new RankedPodcast(i + 1)
            {
                Ranking = ranking,
                Podcast = podcast,
            });
        }
        return ranking;
    }

    public void Dispose() => _httpClient.Dispose();
}
