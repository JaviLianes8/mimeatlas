import mimeatlas


def test_guesses_type_from_a_known_extension() -> None:
    assert mimeatlas.guess_type("report.pdf") == "application/pdf"


def test_guesses_extension_from_a_known_type() -> None:
    assert mimeatlas.guess_extension("application/pdf") == ".pdf"


def test_extension_lookup_is_case_insensitive() -> None:
    assert mimeatlas.guess_type("PHOTO.JPG") == "image/jpeg"


def test_type_lookup_is_case_insensitive() -> None:
    assert mimeatlas.guess_extension("IMAGE/PNG") == ".png"


def test_unknown_extension_returns_none() -> None:
    assert mimeatlas.guess_type("archive.unknownext") is None


def test_unknown_type_returns_none() -> None:
    assert mimeatlas.guess_extension("application/x-nope") is None


def test_path_without_extension_returns_none() -> None:
    assert mimeatlas.guess_type("Makefile") is None


def test_leading_dot_dotfile_has_no_extension() -> None:
    assert mimeatlas.guess_type(".gitignore") is None


def test_handles_posix_directories() -> None:
    assert mimeatlas.guess_type("/var/log/app/output.json") == "application/json"


def test_handles_windows_directories() -> None:
    assert mimeatlas.guess_type(r"C:\\Users\\me\\song.mp3") == "audio/mpeg"


def test_multi_dot_uses_the_final_extension() -> None:
    assert mimeatlas.guess_type("backup.tar.gz") == "application/gzip"


def test_bare_tar_is_recognised() -> None:
    assert mimeatlas.guess_type("backup.tar") == "application/x-tar"


def test_type_parameters_are_ignored() -> None:
    assert mimeatlas.guess_extension("text/html; charset=utf-8") == ".html"


def test_aliased_extensions_share_one_type() -> None:
    assert mimeatlas.guess_type("a.jpeg") == mimeatlas.guess_type("b.jpg")


def test_preferred_extension_is_returned_for_aliases() -> None:
    assert mimeatlas.guess_extension("image/jpeg") == ".jpg"


def test_trailing_dot_has_no_extension() -> None:
    assert mimeatlas.guess_type("weird.") is None
