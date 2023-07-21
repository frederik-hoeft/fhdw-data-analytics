using System.ComponentModel.DataAnnotations;

namespace SpotifyCrawler.Output;

public record PodcastDataSet(DateTime CollectedAt)
{
    [Key]
    public int Id { get; set; }
    public virtual List<PodcastRanking> Rankings { get; set; } = null!;
}