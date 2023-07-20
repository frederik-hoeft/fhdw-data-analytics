namespace SpotifyCrawler.Output;

public record DataRoot(DateTime CollectedAt, List<PodcastRanking> Rankings);