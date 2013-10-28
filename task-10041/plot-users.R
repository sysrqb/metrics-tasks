# Copyright 2013 The Tor Project
# See LICENSE for licensing information

args <- commandArgs(TRUE)
if (length(args) < 5) {
  print("Not enough arguments. See README for usage instructions and examples.")
  print("  Rscript plot-users.R direct 2013-07-01 2013-09-30 us on 1.png")
  print("  Rscript plot-users.R bridge 2013-01-01 2013-03-31 all 2.png")
  quit()
}

require(ggplot2, quietly = TRUE)
require(reshape, quietly = TRUE, warn.conflicts = FALSE)
options(scipen = 15)

countrylist <- list(
  "ad" = "Andorra",
  "ae" = "the United Arab Emirates",
  "af" = "Afghanistan",
  "ag" = "Antigua and Barbuda",
  "ai" = "Anguilla",
  "al" = "Albania",
  "am" = "Armenia",
  "an" = "the Netherlands Antilles",
  "ao" = "Angola",
  "aq" = "Antarctica",
  "ar" = "Argentina",
  "as" = "American Samoa",
  "at" = "Austria",
  "au" = "Australia",
  "aw" = "Aruba",
  "ax" = "the Aland Islands",
  "az" = "Azerbaijan",
  "ba" = "Bosnia and Herzegovina",
  "bb" = "Barbados",
  "bd" = "Bangladesh",
  "be" = "Belgium",
  "bf" = "Burkina Faso",
  "bg" = "Bulgaria",
  "bh" = "Bahrain",
  "bi" = "Burundi",
  "bj" = "Benin",
  "bl" = "Saint Bartelemey",
  "bm" = "Bermuda",
  "bn" = "Brunei",
  "bo" = "Bolivia",
  "br" = "Brazil",
  "bs" = "the Bahamas",
  "bt" = "Bhutan",
  "bv" = "the Bouvet Island",
  "bw" = "Botswana",
  "by" = "Belarus",
  "bz" = "Belize",
  "ca" = "Canada",
  "cc" = "the Cocos (Keeling) Islands",
  "cd" = "the Democratic Republic of the Congo",
  "cf" = "Central African Republic",
  "cg" = "Congo",
  "ch" = "Switzerland",
  "ci" = "Côte d'Ivoire",
  "ck" = "the Cook Islands",
  "cl" = "Chile",
  "cm" = "Cameroon",
  "cn" = "China",
  "co" = "Colombia",
  "cr" = "Costa Rica",
  "cu" = "Cuba",
  "cv" = "Cape Verde",
  "cx" = "the Christmas Island",
  "cy" = "Cyprus",
  "cz" = "the Czech Republic",
  "de" = "Germany",
  "dj" = "Djibouti",
  "dk" = "Denmark",
  "dm" = "Dominica",
  "do" = "the Dominican Republic",
  "dz" = "Algeria",
  "ec" = "Ecuador",
  "ee" = "Estonia",
  "eg" = "Egypt",
  "eh" = "the Western Sahara",
  "er" = "Eritrea",
  "es" = "Spain",
  "et" = "Ethiopia",
  "fi" = "Finland",
  "fj" = "Fiji",
  "fk" = "the Falkland Islands (Malvinas)",
  "fm" = "the Federated States of Micronesia",
  "fo" = "the Faroe Islands",
  "fr" = "France",
  "fx" = "Metropolitan France",
  "ga" = "Gabon",
  "gb" = "the United Kingdom",
  "gd" = "Grenada",
  "ge" = "Georgia",
  "gf" = "French Guiana",
  "gg" = "Guernsey",
  "gh" = "Ghana",
  "gi" = "Gibraltar",
  "gl" = "Greenland",
  "gm" = "Gambia",
  "gn" = "Guinea",
  "gp" = "Guadeloupe",
  "gq" = "Equatorial Guinea",
  "gr" = "Greece",
  "gs" = "South Georgia and the South Sandwich Islands",
  "gt" = "Guatemala",
  "gu" = "Guam",
  "gw" = "Guinea-Bissau",
  "gy" = "Guyana",
  "hk" = "Hong Kong",
  "hm" = "Heard Island and McDonald Islands",
  "hn" = "Honduras",
  "hr" = "Croatia",
  "ht" = "Haiti",
  "hu" = "Hungary",
  "id" = "Indonesia",
  "ie" = "Ireland",
  "il" = "Israel",
  "im" = "the Isle of Man",
  "in" = "India",
  "io" = "the British Indian Ocean Territory",
  "iq" = "Iraq",
  "ir" = "Iran",
  "is" = "Iceland",
  "it" = "Italy",
  "je" = "Jersey",
  "jm" = "Jamaica",
  "jo" = "Jordan",
  "jp" = "Japan",
  "ke" = "Kenya",
  "kg" = "Kyrgyzstan",
  "kh" = "Cambodia",
  "ki" = "Kiribati",
  "km" = "Comoros",
  "kn" = "Saint Kitts and Nevis",
  "kp" = "North Korea",
  "kr" = "the Republic of Korea",
  "kw" = "Kuwait",
  "ky" = "the Cayman Islands",
  "kz" = "Kazakhstan",
  "la" = "Laos",
  "lb" = "Lebanon",
  "lc" = "Saint Lucia",
  "li" = "Liechtenstein",
  "lk" = "Sri Lanka",
  "lr" = "Liberia",
  "ls" = "Lesotho",
  "lt" = "Lithuania",
  "lu" = "Luxembourg",
  "lv" = "Latvia",
  "ly" = "Libya",
  "ma" = "Morocco",
  "mc" = "Monaco",
  "md" = "the Republic of Moldova",
  "me" = "Montenegro",
  "mf" = "Saint Martin",
  "mg" = "Madagascar",
  "mh" = "the Marshall Islands",
  "mk" = "Macedonia",
  "ml" = "Mali",
  "mm" = "Burma",
  "mn" = "Mongolia",
  "mo" = "Macau",
  "mp" = "the Northern Mariana Islands",
  "mq" = "Martinique",
  "mr" = "Mauritania",
  "ms" = "Montserrat",
  "mt" = "Malta",
  "mu" = "Mauritius",
  "mv" = "the Maldives",
  "mw" = "Malawi",
  "mx" = "Mexico",
  "my" = "Malaysia",
  "mz" = "Mozambique",
  "na" = "Namibia",
  "nc" = "New Caledonia",
  "ne" = "Niger",
  "nf" = "Norfolk Island",
  "ng" = "Nigeria",
  "ni" = "Nicaragua",
  "nl" = "the Netherlands",
  "no" = "Norway",
  "np" = "Nepal",
  "nr" = "Nauru",
  "nu" = "Niue",
  "nz" = "New Zealand",
  "om" = "Oman",
  "pa" = "Panama",
  "pe" = "Peru",
  "pf" = "French Polynesia",
  "pg" = "Papua New Guinea",
  "ph" = "the Philippines",
  "pk" = "Pakistan",
  "pl" = "Poland",
  "pm" = "Saint Pierre and Miquelon",
  "pn" = "the Pitcairn Islands",
  "pr" = "Puerto Rico",
  "ps" = "the Palestinian Territory",
  "pt" = "Portugal",
  "pw" = "Palau",
  "py" = "Paraguay",
  "qa" = "Qatar",
  "re" = "Reunion",
  "ro" = "Romania",
  "rs" = "Serbia",
  "ru" = "Russia",
  "rw" = "Rwanda",
  "sa" = "Saudi Arabia",
  "sb" = "the Solomon Islands",
  "sc" = "the Seychelles",
  "sd" = "Sudan",
  "se" = "Sweden",
  "sg" = "Singapore",
  "sh" = "Saint Helena",
  "si" = "Slovenia",
  "sj" = "Svalbard and Jan Mayen",
  "sk" = "Slovakia",
  "sl" = "Sierra Leone",
  "sm" = "San Marino",
  "sn" = "Senegal",
  "so" = "Somalia",
  "sr" = "Suriname",
  "st" = "São Tomé and Príncipe",
  "sv" = "El Salvador",
  "sy" = "the Syrian Arab Republic",
  "sz" = "Swaziland",
  "tc" = "Turks and Caicos Islands",
  "td" = "Chad",
  "tf" = "the French Southern Territories",
  "tg" = "Togo",
  "th" = "Thailand",
  "tj" = "Tajikistan",
  "tk" = "Tokelau",
  "tl" = "East Timor",
  "tm" = "Turkmenistan",
  "tn" = "Tunisia",
  "to" = "Tonga",
  "tr" = "Turkey",
  "tt" = "Trinidad and Tobago",
  "tv" = "Tuvalu",
  "tw" = "Taiwan",
  "tz" = "the United Republic of Tanzania",
  "ua" = "Ukraine",
  "ug" = "Uganda",
  "um" = "the United States Minor Outlying Islands",
  "us" = "the United States",
  "uy" = "Uruguay",
  "uz" = "Uzbekistan",
  "va" = "Vatican City",
  "vc" = "Saint Vincent and the Grenadines",
  "ve" = "Venezuela",
  "vg" = "the British Virgin Islands",
  "vi" = "the United States Virgin Islands",
  "vn" = "Vietnam",
  "vu" = "Vanuatu",
  "wf" = "Wallis and Futuna",
  "ws" = "Samoa",
  "ye" = "Yemen",
  "yt" = "Mayotte",
  "za" = "South Africa",
  "zm" = "Zambia",
  "zw" = "Zimbabwe")

countryname <- function(country) {
  res <- countrylist[[country]]
  if (is.null(res))
    res <- "no-man's-land"
  res
}

plot_direct_users <- function(start, end, country, events, path) {
  u <- read.csv("direct-users.csv.gz", stringsAsFactors = FALSE)
  u <- u[u$date >= start & u$date <= end, ]
  u <- melt(u, id.vars = "date")
  u <- u[u$variable %in% c(country, "all"), ]
  a <- u[u$variable == "all", ]
  if (country != "all")
    u <- u[u$variable == country, ]
  u <- data.frame(date = u$date, users = u$value)
  dates <- seq(from = as.Date(start, "%Y-%m-%d"),
      to = as.Date(end, "%Y-%m-%d"), by="1 day")
  missing <- setdiff(dates, as.Date(a$date))
  if (length(missing) > 0)
    u <- rbind(u,
        data.frame(date = as.Date(missing, origin = "1970-01-01"),
        users = NA))
  missing <- setdiff(dates, as.Date(u$date))
  if (length(missing) > 0)
    u <- rbind(u,
        data.frame(date = as.Date(missing, origin = "1970-01-01"),
        users = 0))
  title <- ifelse(country == "all",
    "Directly connecting users from all countries\n",
    paste("Directly connecting users from ", countryname(country), "\n",
      sep = ""))
  max_y <- ifelse(length(na.omit(u$users)) == 0, 0,
      max(u$users, na.rm = TRUE))
  plot <- ggplot(u, aes(x = as.Date(date, "%Y-%m-%d"), y = users))
  if (length(na.omit(u$users)) > 0 & events != "off" & country != "all") {
    r <- read.csv("direct-users-ranges.csv.gz", stringsAsFactors = FALSE)
    r <- r[r$date >= start & r$date <= end & r$country == country,
        c("date", "minusers", "maxusers")]
    r[r$minusers < 0, "minusers"] <- 0
    r <- cast(rbind(melt(u, id.vars = "date"), melt(r, id.vars = "date")))
    upturns <- r[r$users > r$maxusers, 1:2]
    downturns <- r[r$users < r$minusers, 1:2]
    if (events == "on") {
      if (length(r$maxusers) > 0)
        max_y <- max(max_y, max(r$maxusers, na.rm = TRUE))
      plot <- plot +
        geom_ribbon(data = r, aes(ymin = minusers,
            ymax = maxusers), fill = "gray")
    }
    if (length(upturns$date) > 0)
      plot <- plot +
          geom_point(data = upturns, aes(x = as.Date(date), y = users), size = 5,
          colour = "dodgerblue2")
    if (length(downturns$date) > 0)
      plot <- plot +
          geom_point(data = downturns, aes(x = as.Date(date), y = users), size = 5,
          colour = "firebrick2")
  }
  plot <- plot +
    geom_line(size = 1) +
    scale_x_date(name = paste("\nThe Tor Project - ",
        "https://metrics.torproject.org/", sep = "")) +
    scale_y_continuous(name = "", limits = c(0, max_y)) +
    ggtitle(title)
  print(plot)
  ggsave(filename = path, width = 8, height = 5, dpi = 72)
}

plot_bridge_users <- function(start, end, country, path) {
  b <- read.csv("bridge-users.csv.gz", stringsAsFactors = FALSE)
  b <- b[b$date >= start & b$date <= end, ]
  b <- melt(b, id.vars = "date")
  b <- b[b$variable %in% c(country, "all"), ]
  bridgeusers <- data.frame(date = as.Date(b$date), users = b$value)
  dates <- seq(from = as.Date(start, "%Y-%m-%d"),
      to = as.Date(end, "%Y-%m-%d"), by="1 day")
  missing <- setdiff(dates, bridgeusers$date)
  if (length(missing) > 0)
    bridgeusers <- rbind(bridgeusers,
        data.frame(date = as.Date(missing, origin = "1970-01-01"),
        users = NA))
  title <- ifelse(country == "all",
    "Bridge users from all countries\n",
    paste("Bridge users from ", countryname(country), "\n", sep = ""))
  ggplot(bridgeusers, aes(x = as.Date(date, "%Y-%m-%d"), y = users)) +
    geom_line(size = 1) +
    scale_x_date(name = paste("\nThe Tor Project - ",
        "https://metrics.torproject.org/", sep = "")) +
    scale_y_continuous(name = "", limits = c(0,
        ifelse(length(na.omit(bridgeusers$users)) == 0, 0,
        max(bridgeusers$users, na.rm = TRUE)))) +
    ggtitle(title)
  ggsave(filename = path, width = 8, height = 5, dpi = 72)
}

if (args[1] == "direct") {
  plot_direct_users(start = args[2], end = args[3], country = args[4],
                    events = args[5], path = args[6])
} else if (args[1] == "bridge") {
  plot_bridge_users(start = args[2], end = args[3], country = args[4],
                    path = args[5])
}

