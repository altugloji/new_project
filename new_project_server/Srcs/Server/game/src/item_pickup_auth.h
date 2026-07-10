#pragma once

// Validates the authenticated HEADER_CG_ITEM_PICKUP_AUTH payload and advances the
// per-connection pickup sequence. Returns the decoded ground-item VID on success.
bool ValidateItemPickupAuth(LPCHARACTER ch, const char* data, DWORD& outVID);

// Emergency fallback for the fixed-size authenticated packet while validation
// is disabled. Keeps the sequence synchronized for a later runtime re-enable.
bool DecodeItemPickupAuthFallback(LPCHARACTER ch, const char* data, DWORD& outVID);

// Applies the secure-mode policy to a legacy five-byte pickup attempt.
void RejectLegacyItemPickup(LPCHARACTER ch, DWORD vid);
