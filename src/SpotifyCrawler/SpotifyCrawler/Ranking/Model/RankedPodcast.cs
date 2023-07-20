using System.Text.Json.Serialization;

namespace SpotifyCrawler.Ranking.Model;

public record RankedPodcast
(
    string ShowUri,
    string ChartRankMove,
    string ShowName,
    string ShowPublisher,
    string ShowImageUrl,
    string ShowDescription
)
{
    public int Rank { get; set; } = -1;
}