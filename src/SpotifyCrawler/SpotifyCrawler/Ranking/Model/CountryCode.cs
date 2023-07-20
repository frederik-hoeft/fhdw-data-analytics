using System.Runtime.Serialization;
using System.Text.Json.Serialization;
using SpotifyCrawler.Ranking.Converters;

namespace SpotifyCrawler.Ranking.Model;

[JsonConverter(typeof(CountryCodeConverter))]
public enum CountryCode
{
    [EnumMember(Value = "ar")] Argentina,
    [EnumMember(Value = "at")] Austria,
    [EnumMember(Value = "ca")] Canada,
    [EnumMember(Value = "cl")] Chile,
    [EnumMember(Value = "co")] Colombia,
    [EnumMember(Value = "dk")] Denmark,
    [EnumMember(Value = "fi")] Finland,
    [EnumMember(Value = "fr")] France,
    [EnumMember(Value = "id")] Indonesia,
    [EnumMember(Value = "ie")] Ireland,
    [EnumMember(Value = "in")] India,
    [EnumMember(Value = "it")] Italy,
    [EnumMember(Value = "jp")] Japan,
    [EnumMember(Value = "nl")] Netherlands,
    [EnumMember(Value = "no")] Norway,
    [EnumMember(Value = "nz")] NewZealand,
    [EnumMember(Value = "ph")] Philippines,
    [EnumMember(Value = "pl")] Poland,
    [EnumMember(Value = "es")] Spain,
    [EnumMember(Value = "us")] UnitedStates
}