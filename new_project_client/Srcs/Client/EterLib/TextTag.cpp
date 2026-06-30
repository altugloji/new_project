#include "stdafx.h"
#include "TextTag.h"
#include "Util.h"

int GetTextTag(const wchar_t * src, int maxLen, int & tagLen, std::wstring & extraInfo)
{
    tagLen = 1;

    if (maxLen < 2 || *src != L'|')
        return TEXT_TAG_PLAIN;

    const wchar_t * cur = ++src;

    if (*cur == L'c') // color
    {
        if (maxLen < 10)
            return TEXT_TAG_PLAIN;

        tagLen = 10;
        extraInfo.assign(++cur, 8);
        return TEXT_TAG_COLOR;
    }
    else if (*cur == L'|')
    {
        tagLen = 2;
        return TEXT_TAG_TAG;
    }
    else if (*cur == L'r') // restore color
    {
        tagLen = 2;
        return TEXT_TAG_RESTORE_COLOR;
    }
    else if (*cur == L'H')
    {
        tagLen = 2;
        return TEXT_TAG_HYPERLINK_START;
    }
    else if (*cur == L'h') // end of hyperlink
    {
        tagLen = 2;
        return TEXT_TAG_HYPERLINK_END;
    }
#ifdef ENABLE_EMOJI_SYSTEM
	else if (*cur == L'E') // emoji |Epath/emo|e
	{
		tagLen = 2;
		return TEXT_TAG_EMOJI_START;
	}
	else if (*cur == L'e') // end of emoji
	{
		tagLen = 2;
		return TEXT_TAG_EMOJI_END;
	}
#endif

    return TEXT_TAG_PLAIN;
}

std::wstring GetTextTagOutputString(const wchar_t * src, int src_len)
{
    int len;
	std::wstring dst;
	std::wstring extraInfo;
    int output_len = 0;
    int hyperlinkStep = 0;

    for (int i = 0; i < src_len; )
    {
	    const int tag = GetTextTag(&src[i], src_len - i, len, extraInfo);

        if (tag == TEXT_TAG_PLAIN || tag == TEXT_TAG_TAG)
        {
            if (hyperlinkStep == 0)
			{
                ++output_len;
				dst += src[i];
			}
        }
        else if (tag == TEXT_TAG_HYPERLINK_START)
            hyperlinkStep = 1;
        else if (tag == TEXT_TAG_HYPERLINK_END)
            hyperlinkStep = 0;
#ifdef ENABLE_EMOJI_SYSTEM
		else if (tag == TEXT_TAG_EMOJI_START)
			hyperlinkStep = 1;
		else if (tag == TEXT_TAG_EMOJI_END)
			hyperlinkStep = 0;
#endif

        i += len;
    }
	return dst;
}

int GetTextTagInternalPosFromRenderPos(const wchar_t * src, int src_len, int offset)
{
    int len;
	std::wstring dst;
	std::wstring extraInfo;
    int output_len = 0;
    int hyperlinkStep = 0;
	bool color_tag = false;
	bool reversed_span = false;
	int internal_offset = 0;

    for (int i = 0; i < src_len; )
    {
	    const int tag = GetTextTag(&src[i], src_len - i, len, extraInfo);

        if (tag == TEXT_TAG_COLOR)
		{
			if (!reversed_span)
			{
				color_tag = true;
				internal_offset = i;
			}
		}
		else if (tag == TEXT_TAG_RESTORE_COLOR)
		{
			color_tag = false;
		}
        else if (tag == TEXT_TAG_PLAIN || tag == TEXT_TAG_TAG)
        {
            if (hyperlinkStep == 0)
			{
				if (!color_tag && !reversed_span)
					internal_offset = i;

				if (offset <= output_len)
					return internal_offset;

                ++output_len;
				dst += src[i];
			}
        }
        else if (tag == TEXT_TAG_HYPERLINK_START)
            hyperlinkStep = 1;
        else if (tag == TEXT_TAG_HYPERLINK_END)
        {
            hyperlinkStep = 0;
            if (!reversed_span && !color_tag && i + 3 < src_len && src[i + 2] == L'|' && src[i + 3] == L'r')
            {
                // Reversed Arabic link opener "|h|r" (color_tag false rules
                // out the forward closer "...|h|r"): pin the cursor in front
                // of the whole block; its [Name] is not enterable, same as a
                // forward link's [Name] inside |c...|r.
                reversed_span = true;
                internal_offset = i;
            }
            else if (reversed_span)
                reversed_span = false;
        }
#ifdef ENABLE_EMOJI_SYSTEM
		else if (tag == TEXT_TAG_EMOJI_START)
			hyperlinkStep = 1;
		else if (tag == TEXT_TAG_EMOJI_END)
			hyperlinkStep = 0;
#endif

        i += len;
    }

	return internal_offset;
}

int GetTextTagOutputLen(const wchar_t * src, int src_len)
{
    int len;
    std::wstring extraInfo;
    int output_len = 0;
    int hyperlinkStep = 0;

    for (int i = 0; i < src_len; )
    {
	    const int tag = GetTextTag(&src[i], src_len - i, len, extraInfo);

        if (tag == TEXT_TAG_PLAIN || tag == TEXT_TAG_TAG)
        {
            if (hyperlinkStep == 0)
                ++output_len;
        }
        else if (tag == TEXT_TAG_HYPERLINK_START)
            hyperlinkStep = 1;
        else if (tag == TEXT_TAG_HYPERLINK_END)
            hyperlinkStep = 0;
#ifdef ENABLE_EMOJI_SYSTEM
		else if (tag == TEXT_TAG_EMOJI_START)
			hyperlinkStep = 1;
		else if (tag == TEXT_TAG_EMOJI_END)
			hyperlinkStep = 0;
#endif

        i += len;
    }
    return output_len;
}

int FindColorTagStartPosition(const wchar_t * src, int src_len)
{
    if (src_len < 2)
        return 0;

    const wchar_t * cur = src;

    if (*(cur - 1) == L'|')
    {
        wchar_t wcEnd = *cur;
        wchar_t wcStart = 0;

        if (wcEnd == L'r')
            wcStart = L'c';
        else if (wcEnd == L'h')
            wcStart = L'h';

        if (wcStart != 0)
        {
            int len = src_len;

            if (len >= 2 && *(cur - 2) == L'|')
                return 1;

            cur -= 2;
            len -= 2;

            while (len > 1)
            {
                if (*cur == wcStart && *(cur - 1) == L'|')
                    return (src - cur) + 1;

                --cur;
                --len;
            }

            // No opening tag exists before this end-tag. For "|r" that is
            // the reversed Arabic link opener "|h|r" (its |c lies AFTER it,
            // see playerGetItemLink CP_ARABIC format) - skip it as one
            // atomic unit. Anything else: step over just the 2-char tag.
            // Returning src_len here flung the cursor to position 0 and the
            // next backspace deleted the first character of the buffer.
            if (wcEnd == L'r' && src_len >= 4 && *(src - 2) == L'h' && *(src - 3) == L'|')
                return 3;
            return 1;
        }

        if (wcEnd == L'H' || wcEnd == L'c')
            return 1;
    }
    else if (*cur == L'|' && *(cur - 1) == L'|')
        return 1;

    return 0;
}

int FindColorTagEndPosition(const wchar_t * src, int src_len)
{
	const wchar_t * cur = src;

	// @fixme012
	wchar_t wcStarts = L'c';
	wchar_t wcEnds = L'r';
	if (GetDefaultCodePage() == CP_ARABIC)
	{
		wcStarts = L'h';
		wcEnds = L'h';
	}

	if (src_len >= 4 && *cur == L'|' && *(cur + 1) == wcStarts)
	{
		int left = src_len - 2;
		cur += 2;

		while (left > 1)
		{
			if (*cur == L'|' && *(cur + 1) == wcEnds)
				return (cur - src) + 1;

			--left;
			++cur;
		}
	}
	else if (src_len >= 2 && *cur == L'|' && *(cur + 1) == L'|')
		return 1;

	return 0;
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
