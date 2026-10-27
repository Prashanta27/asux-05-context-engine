import hashlib
import re
import unicodedata

from asux_context_engine.models import ContextItem


class ContextDeduplicator:
    """
    Conservative deduplication for ContextItems.
    Detects exact-content and normalized-text duplicates while safely merging metadata.
    """

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """
        Normalizes text by Unicode NFKC normalization, lowercasing,
        collapsing whitespace, and stripping leading/trailing spaces.
        """
        if not text:
            return ""
        norm = unicodedata.normalize("NFKC", text).lower()
        norm = re.sub(r"\s+", " ", norm).strip()
        return norm

    @classmethod
    def get_exact_hash(cls, text: str) -> str:
        """Returns the SHA-256 hash of the exact string."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def get_normalized_hash(cls, text: str) -> str:
        """Returns the SHA-256 hash of the normalized string."""
        norm_text = cls.normalize_text(text)
        return hashlib.sha256(norm_text.encode("utf-8")).hexdigest()

    def deduplicate(
        self,
        items: list[ContextItem],
        use_normalized: bool = True,
    ) -> list[ContextItem]:
        """
        Deduplicates a list of ContextItems.
        If duplicates are found, conservative merging preserves the item with
        the highest priority, merges non-conflicting metadata, and retains earliest creation.
        """
        if not items:
            return []

        seen_hashes: dict[str, ContextItem] = {}
        ordered_keys: list[str] = []

        for item in items:
            key = (
                self.get_normalized_hash(item.content)
                if use_normalized
                else self.get_exact_hash(item.content)
            )

            # Include context_type in deduplication key so instructions and facts are not conflated
            dedup_key = f"{item.context_type.value}:{key}"

            if dedup_key not in seen_hashes:
                seen_hashes[dedup_key] = item.model_copy(deep=True)
                ordered_keys.append(dedup_key)
            else:
                existing = seen_hashes[dedup_key]
                # Conservative merge: retain highest priority
                merged_priority = max(existing.priority, item.priority)

                # Merge metadata (existing takes precedence, new non-conflicting keys added)
                merged_metadata = dict(item.metadata)
                merged_metadata.update(existing.metadata)

                # Earliest created_at
                earliest_created = min(existing.created_at, item.created_at)

                # Earliest expiration if any
                merged_expires = existing.expires_at
                if item.expires_at is not None:
                    if merged_expires is None:
                        merged_expires = item.expires_at
                    else:
                        merged_expires = min(merged_expires, item.expires_at)

                updated_item = existing.model_copy(
                    update={
                        "priority": merged_priority,
                        "metadata": merged_metadata,
                        "created_at": earliest_created,
                        "expires_at": merged_expires,
                    }
                )
                seen_hashes[dedup_key] = updated_item

        return [seen_hashes[k] for k in ordered_keys]
