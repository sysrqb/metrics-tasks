require(reshape)
t <- read.csv("task-6498-results.csv", stringsAsFactors = FALSE)
t <- t[t$valid_after < paste(Sys.Date() - 1, "23:59:59"), ]
t <- rbind(
  data.frame(t[t$ports == "80-443-554-1755", c(1, 6, 7)], var = "fast"),
  data.frame(t[t$ports == "80-443", c(1, 6, 7)], var = "both"))
r <- cast(t, valid_after ~ var, value = "relays", fun.aggregate = max)
e <- cast(t, valid_after ~ var, value = "exit_prob",
  fun.aggregate = max)
t <- rbind(
  data.frame(valid_after = r$valid_after, value = r$fast,
             variable = "fastnum"),
  data.frame(valid_after = r$valid_after, value = r$both - r$fast,
             variable = "almostnum"),
  data.frame(valid_after = e$valid_after, value = 100 * e$fast,
             variable = "fastprob"),
  data.frame(valid_after = e$valid_after, value = 100 * (e$both - e$fast),
             variable = "almostprob"))
t <- aggregate(list(value = t$value),
  by = list(date = as.Date(cut.Date(as.Date(t$valid_after), "day")),
  variable = t$variable), FUN = median)
t <- cast(t, date ~ variable, value = "value", fun.aggregate = max)
t <- data.frame(date = t$date, round(t[, 2:3], 0), round(t[, 4:5], 2))
write.csv(t, "fast-exits.csv", quote = FALSE, row.names = FALSE)

