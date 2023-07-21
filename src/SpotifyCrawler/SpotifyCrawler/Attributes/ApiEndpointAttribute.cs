namespace SpotifyCrawler.Attributes;

[AttributeUsage(AttributeTargets.Field, Inherited = false, AllowMultiple = false)]
public class ApiEndpointAttribute : Attribute
{
    public string Endpoint { get; }

    public ApiEndpointAttribute(string endpoint) => Endpoint = endpoint;
}
