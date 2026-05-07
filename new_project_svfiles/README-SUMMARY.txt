TODO
- locale.lua -- flame dungeon in german and korean
- guild_war_observer.quest -- translated using locale.lua (no multilan)
- few parts in translate_XX.lua are still in germany


TRANSLATIONS TAKEN FROM:
- https://metin2.dev/topic/22340-translate-lua-15-languages/
- https://metin2.dev/topic/22878-locale_stringtxt-file-in-14-languages/
- https://metin2.dev/topic/30544-summary-thread-quests/
- ChatGPT


FIRST USE
- pick your own locale_string_XX.txt and rename it locale_string.txt
- pick your own translate_XX.lua and rename it translate.lua
- pick your own dragon_soul_table_XX.txt and rename it dragon_soul_table.txt


ERRORS
- QUEST_TEMP when clicking npcs.
  Close and reopen the client.
  The error is in locale_string.txt.
  A corrupted "´Ý±â"; (cancel) string. (last menu option to leave a chat.script)

CHARSETS
- ae 1256
- cz 1250
- de 1252
- dk 1252
- en 1252
- es 1252
- fr 1252
- gr 1253
- hu 1250
- it 1252
- nl 1252
- pl 1250
- pt 1252
- ro 1250 (two accents require a conversion)
- ru koi8-ru
- tr 1254
