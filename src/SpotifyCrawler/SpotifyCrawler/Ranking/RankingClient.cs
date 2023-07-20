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
    }

    public RankedPodcast[] GetRankingForCountry(CountryCode countryCode)
    {
        using HttpRequestMessage request = new(HttpMethod.Get, $"/api/charts/top?region={countryCode.GetEnumMemberValue()}");
        using HttpResponseMessage response = _httpClient.Send(request);
        Console.WriteLine($"{response.StatusCode}: {request.Method} {request.RequestUri}");
        RankedPodcast[] ranking = response.Content.ReadFromJson<RankedPodcast[]>(_jsonOptions)
            ?? throw new InvalidOperationException("failed to deserialize response!");
        for (int i = 0; i < ranking.Length; i++)
        {
            ranking[i].Rank = i;
        }
        return ranking;
    }

    public void Dispose() => _httpClient.Dispose();
}
