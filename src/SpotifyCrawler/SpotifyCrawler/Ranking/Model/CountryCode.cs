using System.Runtime.Serialization;
using System.Text.Json.Serialization;
using SpotifyCrawler.Attributes;
using SpotifyCrawler.Ranking.Converters;

namespace SpotifyCrawler.Ranking.Model;

[JsonConverter(typeof(CountryCodeConverter))]
public enum CountryCode
{
    [JsonValue("ar")] Argentina,
    [JsonValue("at")] Austria,
    [JsonValue("au")] Australia,
    [JsonValue("br")] Brazil,
    [JsonValue("ca")] Canada,
    [JsonValue("cl")] Chile,
    [JsonValue("co")] Colombia,
    [JsonValue("dk")] Denmark,
    [JsonValue("fi")] Finland,
    [JsonValue("fr")] France,
    [JsonValue("de")] Germany,
    [JsonValue("in")] India,
    [JsonValue("id")] Indonesia,
    [JsonValue("ie")] Ireland,
    [JsonValue("it")] Italy,
    [JsonValue("jp")] Japan,
    [JsonValue("mx")] Mexico,
    [JsonValue("nl")] Netherlands,
    [JsonValue("nz")] NewZealand,
    [JsonValue("no")] Norway,
    [JsonValue("ph")] Philippines,
    [JsonValue("pl")] Poland,
    [JsonValue("es")] Spain,
    [JsonValue("se")] Sweden,
    [JsonValue("gb")] UnitedKingdom,
    [JsonValue("us")] UnitedStates
}