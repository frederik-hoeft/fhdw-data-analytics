namespace SpotifyCrawler.Attributes;

[AttributeUsage(AttributeTargets.Field, Inherited = false, AllowMultiple = false)]
public class JsonValueAttribute : Attribute
{
    public string Value { get; }

    public JsonValueAttribute(string value) => Value = value;
}
