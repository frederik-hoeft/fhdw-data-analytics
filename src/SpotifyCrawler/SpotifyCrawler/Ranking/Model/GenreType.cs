using SpotifyCrawler.Attributes;

namespace SpotifyCrawler.Ranking.Model;

public enum GenreType
{
    All = -1,
    Unknown,
    [ApiEndpoint("arts")] Arts,
    [ApiEndpoint("business")] Business,
    [ApiEndpoint("comedy")] Comedy,
    [ApiEndpoint("education")] Education,
    [ApiEndpoint("fiction")] Fiction,
    [ApiEndpoint("health%252520%2526%252520fitness")] HealthAndFitness,
    [ApiEndpoint("history")] History,
    [ApiEndpoint("leisure")] Leisure,
    [ApiEndpoint("music")] Music,
    [ApiEndpoint("news")] News,
    [ApiEndpoint("religion%252520%2526%252520spirituality")] ReligionAndSpirituality,
    [ApiEndpoint("science")] Science,
    [ApiEndpoint("society%252520%2526%252520culture")] SocietyAndCulture,
    [ApiEndpoint("sports")] Sports,
    [ApiEndpoint("technology")] Technology,
    [ApiEndpoint("true%252520crime")] TrueCrime,
    [ApiEndpoint("tv%252520%2526%252520film")] TvAndFilm,
}
