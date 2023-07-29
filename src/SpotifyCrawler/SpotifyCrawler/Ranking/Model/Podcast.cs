using Microsoft.EntityFrameworkCore;
using SpotifyCrawler.Data;
using SpotifyCrawler.SpotifyApi.Models.GetEpisodes;
using System.ComponentModel.DataAnnotations;

namespace SpotifyCrawler.Ranking.Model;

[Index(nameof(ShowUri), IsUnique = true)]
public record Podcast
(
    string ShowUri,
    string ChartRankMove,
    string ShowImageUrl
)
{
    public string ShowName { get; set; } = null!;

    public string ShowPublisher { get; set; } = null!;

    public string ShowDescription { get; set; } = null!;

    public List<RankedPodcast> Rankings { get; set; } = null!;

    public GenreType Genre { get; set; }

    public bool IsExplicit { get; set; }

    [Required]
    public CountryCode Market { get; set; }

    [Key]
    public int Id { get; set; }

    public virtual List<PodcastEpisode> Episodes { get; set; } = null!;
}