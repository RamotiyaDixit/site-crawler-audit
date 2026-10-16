from optimity_scraper.parser import parse_page

HTML = """
<html><head>
<title>  Hello   World </title>
<meta name="description" content="A test page">
<link rel="canonical" href="/canon">
<meta property="og:title" content="OG Title">
<script type="application/ld+json">{"@type": "Organization", "name": "Acme"}</script>
<script type="application/ld+json">{ not valid json </script>
</head><body>
<h1>Main</h1><h2>Sub A</h2><h2>Sub B</h2><h3>Deep</h3>
<a href="/a">A</a> <a href="/a/">A again</a> <a href="https://www.site.test/b#frag">B</a>
<a href="https://other.test/x">External</a>
<a href="mailto:Info@Site.test?subject=hi">mail</a>
<a href="tel:+91 635 301 5499">call</a>
<a href="#top">skip</a> <a href="javascript:void(0)">js</a>
<img src="/i.png" alt="Logo"> <img src="/j.png">
<p>Reach us at sales@site.test or +91 635 301 5499 today.</p>
<script>var ignored = "should not count";</script>
</body></html>
"""


def test_parse_basic_fields():
    page = parse_page(HTML, "https://site.test/", 200, "now")
    assert page.title == "Hello World"
    assert page.meta_description == "A test page"
    assert page.canonical == "https://site.test/canon"
    assert page.og == {"og:title": "OG Title"}
    assert page.headings == {"h1": ["Main"], "h2": ["Sub A", "Sub B"], "h3": ["Deep"]}
    assert page.json_ld == [{"@type": "Organization", "name": "Acme"}]
    assert page.page_type == "home"


def test_links_are_normalised_deduped_and_split():
    page = parse_page(HTML, "https://site.test/", 200, "now")
    assert page.internal_links == ["https://site.test/a", "https://www.site.test/b"]
    assert page.external_links == ["https://other.test/x"]


def test_contacts_and_images():
    page = parse_page(HTML, "https://site.test/", 200, "now")
    assert page.emails == ["info@site.test", "sales@site.test"]
    assert page.phones == ["+91 635 301 5499"]
    assert [i["alt"] for i in page.images] == ["Logo", ""]


def test_word_count_ignores_scripts():
    page = parse_page("<body><p>one two three</p><script>four five</script></body>", "https://site.test/")
    assert page.word_count == 3
