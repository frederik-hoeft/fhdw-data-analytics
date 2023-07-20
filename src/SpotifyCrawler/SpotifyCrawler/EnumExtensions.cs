using System.Reflection;
using System.Runtime.Serialization;

namespace SpotifyCrawler;

public static class EnumExtensions
{
    public static string? GetEnumMemberValue<T>(this T value) where T : Enum
    {
        Type enumType = value.GetType();
        string enumName = value.ToString();

        MemberInfo[] memberInfo = enumType.GetMember(enumName);
        EnumMemberAttribute enumMemberAttribute = (EnumMemberAttribute)memberInfo[0].GetCustomAttribute(typeof(EnumMemberAttribute), false)!;

        return enumMemberAttribute.Value;
    }
}