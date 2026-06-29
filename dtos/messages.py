"""Dapr pub/sub message contracts shared across the OnLooker microservices.

The UI (ui-onlooker) only does I/O: it never talks to an LLM. It stores the
document in Postgres and publishes lightweight events; the Docker components
(embeding-service -> features-extractor -> audience-settings -> develop-analysis)
react to those events over Dapr.

Topic vocabulary (pubsub component name: ``pubsub``):

  document.uploaded     UI            -> embeding-service   (DocumentUploaded)
  embedding.progress    embeding-svc  -> ui                 (ServiceProgress)
  features.extract      embeding-svc  -> features-extractor (CollectionReady)
  features.ready        features-ext  -> audience-settings  (FeaturesReady)
  audience.ready        audience-set  -> develop-analysis   (AudienceReady)
  analysis.ready        develop-anal  -> ui                 (AnalysisReady)
"""

from __future__ import annotations

from pydantic import BaseModel

# Accepted upload formats (extension, no dot).
ACCEPTED_DOC_TYPES = ("txt", "md", "pdf", "pptx", "docx")


class DocumentUploaded(BaseModel):
    """UI -> embeding-service. Only the id + extension travel; bytes live in DB."""

    id_product: str
    doc_type: str  # one of ACCEPTED_DOC_TYPES


class ServiceProgress(BaseModel):
    """Any service -> UI. Success/progress heartbeat shown in the interface."""

    id_product: str
    service: str            # 'embeding-service' | 'features-extractor' | ...
    event: str              # 'started' | 'progress' | 'success' | 'error'
    detail: str = ""
    progress: float = 0.0   # 0..1


class CollectionReady(BaseModel):
    """embeding-service -> features-extractor. Chroma collection is populated."""

    id_product: str
    collection: str
    n_chunks: int = 0


class AudienceSettings(BaseModel):
    """UI -> audience-settings. Empty values fall back to the documented defaults."""

    audience_type: str = ""         # default: globalized
    audience_enviroment: str = ""   # default: globalized
    audience_area: str = ""         # default: globalized
    audience_size: int = 1500       # default: ~1500
    gender_dstn: str = "generic"    # default: generic
    age_dstn: str = "20-45"         # default: 20-45
    main_goal: str = ""             # default: no goal, just the raw scores
    response_goal: str = ""         # default: no goal, just the raw scores


class InsightSelection(BaseModel):
    """UI -> develop-analysis. Which insights the user wants in the report."""

    detect_strengts: bool = False
    detect_weakness: bool = False
    detect_potential: bool = False
    general_report: bool = False


<<<<<<< HEAD
class FeaturesReady(BaseModel):
    """features-extractor -> audience-settings. Features persisted in products.features."""

    id_product: str
    collection: str
    n_features: int = 0


class AudienceReady(BaseModel):
    """audience-settings -> develop-analysis. Per-feature reactions persisted in DB."""

    id_product: str
    n_features: int = 0
    n_groups: int = 0


class AnalysisReady(BaseModel):
    """develop-analysis -> UI. Final insights persisted; the UI reads them from DB."""

    id_product: str
    insights: list[str] = []


=======
>>>>>>> 15f913d (cleaning and restructuring to microservices infrastructure)
__all__ = [
    "ACCEPTED_DOC_TYPES",
    "DocumentUploaded",
    "ServiceProgress",
    "CollectionReady",
    "AudienceSettings",
    "InsightSelection",
<<<<<<< HEAD
    "FeaturesReady",
    "AudienceReady",
    "AnalysisReady",
=======
>>>>>>> 15f913d (cleaning and restructuring to microservices infrastructure)
]
