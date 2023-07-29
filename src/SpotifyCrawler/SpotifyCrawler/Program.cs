using Microsoft.EntityFrameworkCore.Storage;
using SpotifyCrawler;
using SpotifyCrawler.Data;
using SpotifyCrawler.Output;
using SpotifyCrawler.Ranking;
using SpotifyCrawler.Ranking.Model;
using SpotifyCrawler.SpotifyApi;

using SqliteContext dbContext = new();
dbContext.Database.EnsureCreated();
if (!dbContext.Rankings.Any())
{
    using RankingClient rankingClient = new();

    using IDbContextTransaction transaction = dbContext.Database.BeginTransaction();
    PodcastDataSet dataSet = new(DateTime.UtcNow)
    {
        Rankings = new List<PodcastRanking>()
    };
    dbContext.DataSets.Add(dataSet);
    dbContext.SaveChanges();
    transaction.Commit();

    foreach (CountryCode country in Enum.GetValues<CountryCode>())
    {
        using IDbContextTransaction countryTransaction = dbContext.Database.BeginTransaction();
        PodcastRanking ranking = rankingClient.GetRankingForCountry(dbContext, country);
        dataSet.Rankings.Add(ranking);
        int changed = dbContext.SaveChanges();
        Console.WriteLine($"{changed} entries written to DB");
        foreach (GenreType genre in Enum.GetValues<GenreType>())
        {
            if (genre is not GenreType.All and not GenreType.Unknown)
            {
                PodcastRanking? genreRanking = rankingClient.GetRankingForCountry(dbContext, country, genre);
                if (genreRanking is null)
                {
                    Console.WriteLine($"Failed to get ranking for {country} -> {genre}");
                    continue;
                }
                dataSet.Rankings.Add(genreRanking);
                changed = dbContext.SaveChanges();
                Console.WriteLine($"{changed} entries written to DB");
            }
        }
        countryTransaction.Commit();
    }
}
Console.WriteLine("DB already contains ranking information! skipping...");
Console.WriteLine("Fetching episode information...");
Secrets secrets = Secrets.LoadFromFile("secrets.json");
List<Podcast> podcasts = dbContext.Podcasts.Where(p => p.Episodes.Count <= 0).ToList();
if (podcasts.Count > 0)
{
    Console.WriteLine($"{podcasts.Count} podcasts are missing episode information!");
    using SpotifyClient spotifyClient = new(secrets);
    if (!spotifyClient.Authenticate())
    {
        throw new InvalidOperationException("Failed to authenticate to spotify :P");
    }
    for (int i = 0; i < podcasts.Count; i++)
    {
        Podcast podcast = podcasts[i];
        using IDbContextTransaction episodeTransaction = dbContext.Database.BeginTransaction();
        bool success = spotifyClient.TryFetchEpisodes(dbContext, podcast);
        if (success)
        {
            Console.WriteLine($"Fetched episodes for podcast {i + 1} of {podcasts.Count}!");
            episodeTransaction.Commit();
        }
        else
        {
            Console.WriteLine($"Failed to fetch episodes for podcast {i + 1} of {podcasts.Count}!");
            episodeTransaction.Rollback();
        }
    }
}
else
{
    Console.WriteLine("No missing episode information found. Nothing to do. Bye :P");
}
Console.WriteLine($"{nameof(SpotifyCrawler)} is exiting...");