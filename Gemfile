source "https://rubygems.org"

# Pin Jekyll to a recent stable line. GitHub Actions' Pages build uses
# `github-pages` gem, but for plain Pages-via-Actions deploys we can use
# jekyll directly which gives us newer features.
gem "jekyll", "~> 4.3"

# Plugins listed in _config.yml
group :jekyll_plugins do
  gem "jekyll-feed", "~> 0.17"
  gem "jekyll-seo-tag", "~> 2.8"
  gem "jekyll-sitemap", "~> 1.4"
  gem "jekyll-toc", "~> 0.19"
end

# Required on newer Ruby
gem "webrick", "~> 1.8"

# Fixes for Windows + JRuby (no-ops on Linux)
platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end
