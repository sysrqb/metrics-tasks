require(ggplot2)
data <- read.csv("s2012.csv", header=TRUE)

# frac_relays
p <- ggplot(data, aes(factor(hours), frac_relays))
p + geom_boxplot() + ylab("frac_relays") + xlab("time interval") + ggtitle(2012)
ggsave("2012_frac_relays.png", height=6, width=6)

# frac_cw
p <- ggplot(data, aes(factor(hours), frac_cw))
p + geom_boxplot() + ylab("frac_cw") + xlab("time interval") + ggtitle(2012)
ggsave("2012_frac_cw.png", height=6, width=6)

