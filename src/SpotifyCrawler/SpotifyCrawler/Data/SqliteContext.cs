using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using SpotifyCrawler.Attributes;
using SpotifyCrawler.Output;
using SpotifyCrawler.Ranking.Model;

namespace SpotifyCrawler.Data;

public class SqliteContext : DbContext
{
    public DbSet<PodcastDataSet> DataSets { get; set; }

    public DbSet<PodcastRanking> Rankings { get; set; }

    public DbSet<RankedPodcast> RankedPodcasts { get; set; }

    public DbSet<Podcast> Podcasts { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder) =>
        optionsBuilder
            .UseSqlite("Data Source=rankings.db")
            .EnableSensitiveDataLogging()
            .LogTo(Console.WriteLine, LogLevel.Warning);

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder
            .Entity<PodcastRanking>()
            .Property(e => e.Country)
            .HasConversion(
                v => v.GetAttributeValue<CountryCode, JsonValueAttribute>(attr => attr.Value),
                v => EnumExtensions.ParseFromAttribute<CountryCode, JsonValueAttribute>(v!, attr => attr.Value));

        modelBuilder
            .Entity<PodcastRanking>()
            .Property(e => e.Genre)
            .HasConversion(
                v => v.ToString(),
                v => Enum.Parse<GenreType>(v));

        modelBuilder
            .Entity<Podcast>()
            .Property(e => e.Genre)
            .HasConversion(
                v => v.ToString(),
                v => Enum.Parse<GenreType>(v));
    }
}
