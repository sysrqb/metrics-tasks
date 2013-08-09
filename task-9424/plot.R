require(ggplot2)
library(scales)

plot_graph <- function(indata, xaxis, outfile) {
  indata <- data.frame(
    x = sort(as.numeric(
        as.POSIXct(indata$V1) - as.POSIXct(indata$V3))) / 86400,
    y = (1:length(indata$V2)) / length(indata$V2))
  indata <- indata[indata$y <= 0.9, ]
  ggplot(indata) +
    geom_line(aes(x = x, y = y)) +
  scale_x_continuous(name = paste("\n", xaxis, sep = "")) +
  scale_y_continuous(name = "Fraction of relays\n", limit = c(0, 1),
    labels = percent)
  ggsave(outfile, width = 8, height = 5, dpi = 100)
}

i <- read.csv("input.csv", stringsAsFactors = FALSE, header = FALSE)
plot_graph(i[i$V2 == "first_seen", ], "Lifetime in days",
  "first_seen.png")
plot_graph(i[i$V2 == "last_restarted", ], "Uptime in days",
  "last_restarted.png")

