from app.models.image import Image
from app.models.label import LabelGroup, Label, ImageLabel
from app.models.preprocess import PreprocessScript, PreprocessTask, PreprocessResult
from app.models.corpus import CorpusTemplate, CorpusRecord
from app.models.user import User


def test_models_importable():
    assert Image.__tablename__ == "images"
    assert LabelGroup.__tablename__ == "label_groups"
    assert Label.__tablename__ == "labels"
    assert ImageLabel.__tablename__ == "image_labels"
    assert PreprocessScript.__tablename__ == "preprocess_scripts"
    assert PreprocessTask.__tablename__ == "preprocess_tasks"
    assert PreprocessResult.__tablename__ == "preprocess_results"
    assert CorpusTemplate.__tablename__ == "corpus_templates"
    assert CorpusRecord.__tablename__ == "corpus_records"
    assert User.__tablename__ == "users"