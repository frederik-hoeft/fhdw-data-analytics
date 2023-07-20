using SpotifyCrawler.Output;
using SpotifyCrawler.Ranking;
using SpotifyCrawler.Ranking.Model;
using System.Text.Json;

List<PodcastRanking> rankings = new();
using RankingClient rankingClient = new();
foreach (CountryCode country in Enum.GetValues<CountryCode>())
{
    RankedPodcast[] rankingList = rankingClient.GetRankingForCountry(country);
    PodcastRanking ranking = new(country, rankingList);
    rankings.Add(ranking);
}
DataRoot root = new(DateTime.UtcNow, rankings);

const string outDir = "data";

Directory.CreateDirectory(outDir);

using Stream output = File.OpenWrite(Path.Combine(outDir, $"spotify-rankings.{root.CollectedAt:yyyy-MM-dd+HH-mm-ss}.json"));
JsonSerializer.Serialize(output, root);

DataRoot dummy = new
(
    DateTime.UtcNow,
    new List<PodcastRanking>()
    {
        new PodcastRanking
        (
            CountryCode.UnitedStates, 
            new RankedPodcast[]
            {
                new RankedPodcast
                (
                    "spotify:show:4rOoJ6Egrf8K2IrywzwOMk",
                    "UNCHANGED",
                    "The Joe Rogan Experience",
                    "Joe Rogan",
                    "https://i.scdn.co/image/d3ae59a048dff7e95109aec18803f22bebe82d2f",
                    "The official podcast of comedian Joe Rogan. Follow The Joe Rogan Clips show page for some of the best moments from the episodes."
                )
                {
                    Rank = 1
                }
            }
        )
    }
);

using Stream dummyOutput = File.OpenWrite(Path.Combine(outDir, "spotify-rankings.0000-structure.json"));
JsonSerializer.Serialize(dummyOutput, dummy, new JsonSerializerOptions() { WriteIndented = true });