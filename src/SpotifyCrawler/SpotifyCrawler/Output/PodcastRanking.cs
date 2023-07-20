using SpotifyCrawler.Ranking.Model;

namespace SpotifyCrawler.Output;

public record PodcastRanking(CountryCode Country, RankedPodcast[] Podcasts);