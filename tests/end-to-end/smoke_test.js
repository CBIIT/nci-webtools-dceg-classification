const path = require('path');
const request = require('request');
const should = require('chai').should();
const { expect } = require('chai');
const { Builder, By, Key, until } = require('selenium-webdriver');
const firefox = require('selenium-webdriver/firefox');

describe('SOCcer Smoke Test', function() {
    this.timeout(0);

    before(async function() {
        this.driver = await new Builder()
            .forBrowser('firefox')
            .setFirefoxOptions(new firefox.Options().headless())
            .build();
        this.website = process.env.TEST_WEBSITE.replace(/\/$/, '');
    });

    it('should specify the correct website', async function() {
        const driver = this.driver;
        await driver.get(this.website);
        await driver.wait(until.titleContains('SOCcer'));
        const title = await driver.getTitle();
        title.should.equal('SOCcer - Standardized Occupation Coding for Computer-assisted Epidemiological Research');
    });

    it('should validate the sample file', async function() {
        const driver = this.driver;

        // switch to soccer tab
        const soccerTab = By.id('soccer-tab');
        await driver.wait(until.elementLocated(soccerTab));
        await driver.findElement(soccerTab).click();

        // upload tests/data/example1.csv
        const uploadPath = path.join(process.cwd(), 'tests', 'data', 'example1.csv');
        await driver.findElement(By.name('input-file')).sendKeys(uploadPath);

        // wait until success message is shown
        const resultStatus = By.css('#alerts > .alert');
        await driver.wait(until.elementLocated(resultStatus));
        const resultStatusClass = await driver.findElement(resultStatus).getAttribute('class');
        resultStatusClass.should.contain('alert-success');
    });

    it('should successfully code the sample file', async function() {
        const driver = this.driver;

        // switch to soccer tab
        const submitLocator = By.id('submit');
        await driver.wait(until.elementLocated(submitLocator));

        const submitElement = driver.findElement(submitLocator);
        await driver.wait(until.elementIsEnabled(submitElement));
        await submitElement.click();

        const resultsElement = driver.findElement(By.id('results-container'));
        await driver.wait(until.elementIsVisible(resultsElement));

        // check if we have a valid download link
        const downloadLink = await driver.findElement(By.id('download-link')).getAttribute('href');
        downloadLink.should.not.be.empty;
    });

    after(async function() {
        this.driver.quit();
    })
});