using Microsoft.EntityFrameworkCore.Metadata.Conventions;
using SpotifyCrawler.Ranking.Model;
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

    public static string? GetAttributeValue<TEnum, TAttribute>(this TEnum value, Func<TAttribute, string?> getter) 
        where TEnum : Enum
        where TAttribute : Attribute
    {
        Type enumType = value.GetType();
        string enumName = value.ToString();

        MemberInfo[] memberInfo = enumType.GetMember(enumName);
        TAttribute enumMemberAttribute = (TAttribute)memberInfo[0].GetCustomAttribute(typeof(TAttribute), false)!;

        return getter.Invoke(enumMemberAttribute);
    }

    private static readonly Dictionary<Type, Dictionary<Type, Dictionary<string, object>>> _enumLut = new();

    public static TEnum ParseFromAttribute<TEnum, TAttribute>(string attributeValue, Func<TAttribute, string> getter)
        where TEnum : struct, Enum
        where TAttribute : Attribute
    {
        Type enumType = typeof(TEnum);
        Type attributeType = typeof(TAttribute);
        if (!_enumLut.TryGetValue(enumType, out Dictionary<Type, Dictionary<string, object>>? attributeLut))
        {
            attributeLut = new Dictionary<Type, Dictionary<string, object>>();
            _enumLut.Add(enumType, attributeLut);
        }
        if (!attributeLut.TryGetValue(attributeType, out Dictionary<string, object>? valueLut))
        {
            valueLut = new Dictionary<string, object>();
            attributeLut.Add(attributeType, valueLut);
        }
        if (!valueLut.TryGetValue(attributeValue, out object? _))
        {
            MemberInfo[] memberInfos = enumType.GetMembers();
            TEnum[] values = Enum.GetValues<TEnum>();
            foreach (MemberInfo memberInfo in memberInfos)
            {
                TAttribute? enumMemberAttribute = memberInfo.GetCustomAttribute(typeof(TAttribute), false) as TAttribute;
                if (enumMemberAttribute is not null)
                {
                    string attrValue = getter.Invoke(enumMemberAttribute);
                    foreach (TEnum value in values)
                    {
                        if (memberInfo.Name.Equals(Enum.GetName(value)))
                        {
                            valueLut.Add(attrValue, value);
                            break;
                        }
                    }
                }
            }
        }
        return (TEnum)valueLut[attributeValue];
    }
}