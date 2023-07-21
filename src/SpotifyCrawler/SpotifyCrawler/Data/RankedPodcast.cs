using Microsoft.EntityFrameworkCore;
using SpotifyCrawler.Output;
using SpotifyCrawler.Ranking.Model;

namespace SpotifyCrawler.Data;

[PrimaryKey(nameof(RankingId), nameof(PodcastId))]
public record RankedPodcast(int Rank)
{
    public int RankingId { get; set; }

    public int PodcastId { get; set; }

    public virtual PodcastRanking Ranking { get; set; } = null!;

    public virtual Podcast Podcast { get; set; } = null!;
}