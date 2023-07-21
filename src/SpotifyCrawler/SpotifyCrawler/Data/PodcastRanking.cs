using SpotifyCrawler.Data;
using SpotifyCrawler.Ranking.Model;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SpotifyCrawler.Output;

public record PodcastRanking(GenreType Genre, CountryCode Country)
{
    [Key, DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public int Id { get; set; }
    public List<RankedPodcast> Podcasts { get; set; } = null!;
}