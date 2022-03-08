hugo new site sls-blog
cd sls-blog

## Setup Steps
cd themes
git clone https://github.com/knadh/hugo-ink.git
cd ..
echo "theme = hugo-ink" >> config.toml
hugo new post/hello-world.md
hugo server -D