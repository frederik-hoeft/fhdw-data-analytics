using System.Runtime.CompilerServices;
using System.Text;

namespace SpotifyCrawler.Ranking.Converters;

public unsafe class UnicodeSanitizer
{
    private readonly StringBuilder _builder = new();

    public string EscapeToAscii(string s)
    {
        _builder.Clear();
        for (int i = 0; i < s.Length; i++)
        {
            char c = s[i];
            if (char.IsAscii(c))
            {
                _builder.Append(c);
            }
            else
            {
                ulong c64 = c;
                // expand and convert to big endian
                // dcba
                // 00 0a 00 0b 00 0c 00 0d
                ulong buffer = ((c64 & 0xF000) >> 12)
                    | ((c64 & 0x0F00) << 8)
                    | ((c64 & 0x00F0) << 28)
                    | ((c64 & 0x000F) << 48);

                buffer = ToHexCharBranchlessX8(buffer) & 0x00FF00FF_00FF00FFuL;

                _builder.Append("\\u")
                    .Append(new Span<char>((char*)&buffer, 4));
            }
        }
        return _builder.ToString();
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static ulong ToHexCharBranchlessX8(ulong y)
    {
        ulong mask8 = (~((y >>> 3) & ((y >>> 2) | (y >>> 1)) & 0x01010101_01010101uL) & 0x7F7F7F7F_7F7F7F7FuL) + 0x01010101_01010101uL;
        return (0x30303030_30303030uL ^ (mask8 & 0x70707070_70707070uL)) | (y - (0x09090909_09090909uL & mask8));
    }
}
