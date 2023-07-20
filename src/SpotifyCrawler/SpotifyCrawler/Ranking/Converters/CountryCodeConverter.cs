using System.Text.Json;
using System.Text.Json.Serialization;
using SpotifyCrawler.Ranking.Model;

namespace SpotifyCrawler.Ranking.Converters;

public class CountryCodeConverter : JsonConverter<CountryCode>
{
    public override CountryCode Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => throw new NotImplementedException();

    public override void Write(Utf8JsonWriter writer, CountryCode value, JsonSerializerOptions options) =>
        writer.WriteStringValue(value.GetEnumMemberValue());
}