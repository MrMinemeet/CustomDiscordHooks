// @ts-check
/**
 * This file is the entry point for DailyMensa.
 * It automatically scrapes menu data from various sources (e.g. JKU mensa)
 * and sends the menu information to the discord hooks specified in "mensen.txt".
 * 
 * The file is intended to be run as a cron job.
 * The "mensen.txt" must contain only one hook URL per line.
 */
import axios from "axios";
import { JSDOM } from "jsdom";
import { loadHooks, numberToWeekday, sendMessage } from "./util.mjs";

/**
 * Fetches the menu from the JKU Mensa
 * @param {number} dayNumber A week day number [1, 7]
 * @returns {Promise<string>} The menu as a string
 */
async function getJkuMensa(dayNumber) {
	// The "mensen.at" has some internally tested API but its not public and seems to send raw GraphQL queries to the server.
	// Therefore, I stick to scraping the website.
	const URL = "https://www.mensen.at/standort/mensa-jku/"

	let html = "";
	try {
		const response = (await axios.get(URL))
		html = response.data;
	} catch (error) {
		console.error("Error fetching JKU Mensa", error);
		return "Failed to get data from JKU Mensa";
	}
	const dom = new JSDOM(html.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, ""));

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

	const html = (await axios.get(URL)).data;

}

/**
 * Performs the actual fetching and hook call
 * @param {number} dayNumber A week day number [1, 7]
 */
async function getMensen(dayNumber) {
	const hooks = loadHooks("mensen.txt");

	let message = "";

	const jkuMenu = getJkuMensa(dayNumber);
	const raabMenu = getRaabMensa(dayNumber);

	message += `${await jkuMenu}\n\n`;
	message += `${await raabMenu}`;

	for (const hook of await hooks) {
		await sendMessage(hook, message);
	}
}

await getMensen(new Date().getDay());