# Blog App

This is the code for the blog that I host at https://blog.claytondavis.dev

## Initial Setup Steps

### Download and install hugo

```
brew install hugo
```

### Create new site

```
hugo new site sls-blog
cd sls-blog
```

### Add Theme

```
cd themes
git clone https://github.com/knadh/hugo-ink.git
cd ..
echo "theme = hugo-ink" >> config.toml
```
<em>Also ended up coping some files from `/themes` into the root folders</em>

### Create new post

```
hugo new post/hello-world.md
```

### Start local server

```
hugo server -D
```

### Build site

```
hugo -D
```