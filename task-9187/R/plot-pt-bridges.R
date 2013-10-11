# Usage (from parent directory):
#   R --slave -f R/plot-pt-bridges.R
require(ggplot2)
b <- read.csv("pt-bridges.csv", stringsAsFactors = FALSE)
b <- b[substr(b$published, 1, 10) > substr(min(b$published), 1, 10), ]
ggplot(b, aes(x = as.POSIXct(published), y = bridges,
  colour = transport)) +
geom_line() +
scale_x_datetime("") +
scale_y_continuous("") +
scale_colour_hue("") +
ggtitle("Running bridges by pluggable transport\n")
ggsave("pt-bridges.png", width = 8, height = 5, dpi = 100)

