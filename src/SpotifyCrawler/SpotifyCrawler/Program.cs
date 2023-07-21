using Microsoft.EntityFrameworkCore.Storage;
using SpotifyCrawler.Data;
using SpotifyCrawler.Output;
using SpotifyCrawler.Ranking;
using SpotifyCrawler.Ranking.Model;

using SqliteContext dbContext = new();
dbContext.Database.EnsureCreated();
using IDbContextTransaction transaction = dbContext.Database.BeginTransaction();

using RankingClient rankingClient = new();

PodcastDataSet dataSet = new(DateTime.UtcNow)
{
    Rankings = new List<PodcastRanking>()
};
dbContext.DataSets.Add(dataSet);
dbContext.SaveChanges();

foreach (CountryCode country in Enum.GetValues<CountryCode>())
{
    PodcastRanking ranking = rankingClient.GetRankingForCountry(dbContext, country);
    dataSet.Rankings.Add(ranking);
    int changed = dbContext.SaveChanges();
    Console.WriteLine($"{changed} entries insered!");
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
            Console.WriteLine($"{changed} entries insered!");
        }
    }
}
transaction.Commit();
return;