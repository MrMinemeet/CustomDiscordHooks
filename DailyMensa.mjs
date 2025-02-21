// @ts-check
/**
 * This file is the entry point for DailyMensa.
 * It automatically scrapes menu data from various sources (e.g. JKU mensa)
 * and sends the menu information to the discord hooks specified in "mensen.txt".
 * 
 * The file is intended to be run as a cron job.
 * The "mensen.txt" must contain only one hook URL per line.
 */
import { getPagebody, loadHooks, numberToWeekday, sendMessage } from "./util.mjs";

Promise.all([loadHooks("mensen.txt"), getMensen(new Date().getDay())])
	.then(([hooks, message]) => {
		for (const hook of hooks) {
			try {
				sendMessage(hook, message);
			} catch (e) {
				console.warn(`Failed to send message to '${hook}'`);
			}
		}	
	}).catch(e => console.error("Something went very wrong", e));

//------------------------------------------------------------------------------
/**
 * Fetches the menu from the JKU Mensa
 * @param {number} dayNumber A week day number [1, 7]
 * @returns {Promise<string>} The menu as a string
 */
async function getJkuMensa(dayNumber) {
	// The "mensen.at" has some internally tested API but its not public and seems to send raw GraphQL queries to the server.
	// Therefore, I stick to scraping the website.
	const URL = "https://www.mensen.at/standort/mensa-jku/"

	const dom = await getPagebody(URL);
	if (dom == null) {
		return "Could not fetch menu for JKU Mensa";
	}

	const swiper = dom.window.document.querySelector(".swiper-wrapper");
	if (swiper == null || swiper.children.length < dayNumber) {
		return "Could not find menu for JKU Mensa";
	}
	const dayChild = swiper.children[dayNumber - 1];

	// The day consists of N meals (typically menu 1, menu 2, dayplate veggi, dayplate meat, soup)
	let menu = `__**JKU Mensa - ${numberToWeekday(dayNumber)}**__\n`;
	for (const meal of dayChild.children) {
		if (meal.childElementCount === 0) {
			console.info("Skipping empty meal");
			continue;
		}

		// Name of meal is in a child h3 element
		const name = meal.querySelector("h3")?.textContent;
		if (name == null) {
			menu += "No name found\n";
			continue;
		}
		// Description of meal and price are in a "li" child
		const descriptionElement = meal.querySelector("li");
		if (descriptionElement == null) {
			menu += `${name} (No further information found)\n`;
			continue;
		}
		// Sometimes the menu description is split into multiple spans ( but only the direct child spans are relevant)
		const description = Array.from(descriptionElement.children[0].children)
			.filter(c => c.tagName === "SPAN")
			.map((span) => span.textContent?.trim()).join(" ");
		const price = descriptionElement.children[1].querySelector("span")?.textContent || "No price found";

		menu += `* **${name}**\n  ${description} - ${price}\n`;
	}

	return menu;
}

/**
 * Fetches the menu from the Raab Mensa
 * @param {number} dayNumber A week day number [1, 7]
 * @returns {Promise<string>} The menu as a string
 */
async function getRaabMensa(dayNumber) {
	const URL = "https://www.mittag.at/r/raabmensa";

	const dom = await getPagebody(URL);
	if (dom == null) {
		return "Could not fetch menu for Raab Mensa";
	}

	const menus = dom.window.document.querySelector("div.current-menu");
	if (menus == null) {
		return "Could not find menu for Raab Mensa";
	}

	const menusCombined = menus.innerHTML?.split("<br>").filter((line) => line.trim() !== "");
	if (menusCombined == null) {
		return "Could not find menu for Raab Mensa";
	}

	const menu2Idx = menusCombined.findIndex(line => line.includes("MENÜ 2"))
	const menu1Split = menusCombined.slice(0, menu2Idx);
	const menu2Split = menusCombined.slice(menu2Idx);

	// The ".shift" is to remove the menu number from the array
	menu1Split.shift();
	menu2Split.shift();

	let menu = `__**Raab Mensa - ${numberToWeekday(dayNumber)}**__\n`;
	menu += `* **Menü 1**\n`;
	if (menu1Split.length > 0) {
		menu += `  ${menu1Split.join("\n  ")}\n`;
	} else {
		menu += "  Kein Menü 1\n";
	}

	menu += `* **Menü 2**\n`;
	if (menu2Split.length > 0) {
		menu += `  ${menu2Split.join("\n")}\n`;
	} else {
		menu += "  Kein Menü 2\n";
	}

	return menu;
}

/**
 * Performs the actual fetching and hook call
 * @param {number} dayNumber A week day number [1, 7]
 * @returns {Promise<string>} The menus as a string
 */
async function getMensen(dayNumber) {
	let message = "";

	const jkuMenu = getJkuMensa(dayNumber);
	const raabMenu = getRaabMensa(dayNumber);

	try {
		message += `${await jkuMenu}\n\n`;
	} catch (e) {
		console.error(e);
		message += "Something went wrong while fetching the JKU Mensa menu\n";
	}
	try {
		message += `${await raabMenu}`;
	} catch (e) {
		console.error(e);
		message += "Something went wrong while fetching the Raab Mensa menu\n";
	}
	return message;
}